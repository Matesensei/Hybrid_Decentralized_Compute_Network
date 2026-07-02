#!/usr/bin/env python3
"""
DePIN / decentralized GPU compute network simulator.

Purpose
-------
A lightweight Monte Carlo + agent-style model for a proposed P2P GPU/CPU
micro-node network. It focuses on the questions that matter before writing
production Rust:

1. Can home GPUs stay profitable after electricity + amortized hardware cost?
2. What fill-rate can the network achieve under demand/price shocks?
3. Does the internal credit treasury remain solvent under cash-outs?
4. How sensitive is security to verifier committee size, Sybil share, and stake?
5. Is the P2P gossip layer likely to remain connected and low-latency?

The model is intentionally dependency-light: numpy, pandas, matplotlib are enough.
It is not a deterministic forecast; it is a decision tool for comparing designs.

Examples
--------
python depin_network_model.py --scenario base --runs 50 --days 365 --plots --out out/base
python depin_network_model.py --scenario stress --runs 200 --days 730 --out out/stress
python depin_network_model.py --scenario base --runs 20 --days 180 --export-node-regions

Outputs
-------
- timeseries.csv: all daily rows across runs
- summary.csv: per-run KPIs
- scenario.json: resolved configuration
- optional PNG plots when --plots is set

License: MIT-style, use freely.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


# -----------------------------
# Configuration
# -----------------------------


@dataclass(frozen=True)
class Region:
    name: str
    elec_usd_kwh: float
    weight: float


@dataclass(frozen=True)
class GPUModel:
    name: str
    watt: float
    perf_units: float  # normalized GPU-hour capacity multiplier, RTX 4090 ~= 1.0
    capex_usd: float
    weight: float


@dataclass
class Scenario:
    name: str = "base"
    days: int = 365
    n_gpu_nodes: int = 750
    n_cpu_verifiers: int = 250

    # Demand and pricing
    base_daily_demand_gpuh: float = 9_000.0
    demand_growth_annual: float = 1.00  # +100%/year in base
    demand_vol_daily: float = 0.08
    price_elasticity: float = 1.15
    initial_price_usd_gpuh: float = 0.32
    competitor_ceiling_usd_gpuh: float = 0.52
    floor_price_usd_gpuh: float = 0.06
    target_utilization: float = 0.72
    adaptive_pricing_strength: float = 0.035

    # Network/economics
    take_rate: float = 0.12
    cashout_rate_daily: float = 0.055
    stress_cashout_multiplier: float = 2.5
    initial_treasury_usdc: float = 25_000.0
    initial_credits: float = 10_000.0
    reserve_yield_apy: float = 0.035
    hw_efficiency_gain_annual: float = 0.25
    capex_amort_months: float = 30.0
    uptime_mean: float = 0.86
    uptime_sd: float = 0.10

    # Node behavior
    min_margin_for_stability_usd_gpuh: float = 0.015
    churn_base_daily: float = 0.006
    churn_unprofitable_multiplier: float = 5.0
    onboarding_rate_daily: float = 0.002

    # P2P network model
    gossip_degree: float = 8.0
    direct_connection_success: float = 0.86
    direct_rtt_ms: float = 55.0
    relay_rtt_ms: float = 180.0
    gossip_overhead_factor: float = 1.45
    avg_msg_size_bytes: int = 420
    receipts_per_gpuh: float = 1.0

    # Verification/security
    verifier_committee_k: int = 7
    verify_sampling_rate: float = 0.18
    lazy_worker_rate: float = 0.015
    sybil_fake_nodes: int = 0
    sybil_detection_daily: float = 0.05
    stake_required_usd: float = 25.0
    attacker_budget_usd: float = 2_500.0
    slashing_loss_usd: float = 25.0

    # Regional/GPU mix
    regions: List[Region] = field(default_factory=list)
    gpus: List[GPUModel] = field(default_factory=list)


def default_regions() -> List[Region]:
    # Rough current-style ranges. Replace with your own electricity dataset later.
    return [
        Region("Finland", 0.09, 0.08),
        Region("Hungary", 0.16, 0.10),
        Region("Austria", 0.24, 0.10),
        Region("Germany", 0.31, 0.16),
        Region("US_low_cost", 0.12, 0.20),
        Region("US_average", 0.18, 0.16),
        Region("Nordics/cheap", 0.07, 0.08),
        Region("Other_EU", 0.22, 0.12),
    ]


def default_gpus() -> List[GPUModel]:
    return [
        GPUModel("RTX_3060_12GB", watt=170, perf_units=0.25, capex_usd=240, weight=0.20),
        GPUModel("RTX_3070", watt=220, perf_units=0.38, capex_usd=310, weight=0.12),
        GPUModel("RTX_3080", watt=320, perf_units=0.55, capex_usd=430, weight=0.12),
        GPUModel("RTX_3090", watt=350, perf_units=0.75, capex_usd=650, weight=0.16),
        GPUModel("RTX_4070_Ti", watt=285, perf_units=0.62, capex_usd=700, weight=0.12),
        GPUModel("RTX_4080", watt=320, perf_units=0.82, capex_usd=900, weight=0.10),
        GPUModel("RTX_4090", watt=430, perf_units=1.00, capex_usd=1_700, weight=0.14),
        GPUModel("RTX_5090", watt=575, perf_units=1.35, capex_usd=2_200, weight=0.04),
    ]


def scenario_preset(name: str) -> Scenario:
    s = Scenario(name=name, regions=default_regions(), gpus=default_gpus())
    if name == "bear":
        s.base_daily_demand_gpuh = 3_800
        s.demand_growth_annual = -0.35
        s.demand_vol_daily = 0.15
        s.competitor_ceiling_usd_gpuh = 0.30
        s.initial_price_usd_gpuh = 0.26
        s.cashout_rate_daily = 0.085
        s.stress_cashout_multiplier = 3.2
        s.hw_efficiency_gain_annual = 0.20
        s.take_rate = 0.10
        s.onboarding_rate_daily = 0.0005
    elif name == "bull":
        s.base_daily_demand_gpuh = 14_000
        s.demand_growth_annual = 4.50
        s.demand_vol_daily = 0.10
        s.competitor_ceiling_usd_gpuh = 0.68
        s.initial_price_usd_gpuh = 0.38
        s.cashout_rate_daily = 0.040
        s.hw_efficiency_gain_annual = 0.35
        s.onboarding_rate_daily = 0.006
        s.n_gpu_nodes = 1_200
        s.n_cpu_verifiers = 400
    elif name == "stress":
        s.base_daily_demand_gpuh = 7_500
        s.demand_growth_annual = 0.25
        s.demand_vol_daily = 0.20
        s.competitor_ceiling_usd_gpuh = 0.28
        s.initial_price_usd_gpuh = 0.30
        s.cashout_rate_daily = 0.10
        s.stress_cashout_multiplier = 4.0
        s.initial_treasury_usdc = 10_000
        s.initial_credits = 18_000
        s.lazy_worker_rate = 0.04
        s.sybil_fake_nodes = 350
        s.attacker_budget_usd = 8_000
        s.stake_required_usd = 20
        s.verifier_committee_k = 5
        s.verify_sampling_rate = 0.10
        s.direct_connection_success = 0.78
    elif name == "security":
        s.base_daily_demand_gpuh = 8_500
        s.lazy_worker_rate = 0.05
        s.sybil_fake_nodes = 800
        s.attacker_budget_usd = 50_000
        s.stake_required_usd = 50
        s.verifier_committee_k = 9
        s.verify_sampling_rate = 0.25
        s.sybil_detection_daily = 0.025
    elif name == "base":
        pass
    else:
        raise ValueError(f"Unknown scenario preset: {name}")
    return s


# -----------------------------
# Helpers
# -----------------------------


def normalize_weights(weights: Iterable[float]) -> np.ndarray:
    arr = np.array(list(weights), dtype=float)
    total = arr.sum()
    if total <= 0:
        raise ValueError("weights must sum to > 0")
    return arr / total


def choose_weighted(rng: np.random.Generator, items: List, n: int) -> np.ndarray:
    weights = normalize_weights([x.weight for x in items])
    return rng.choice(len(items), size=n, p=weights)


def logistic(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


def daily_growth_factor(annual_growth: float) -> float:
    # annual_growth=1.0 means +100%/yr => 2x over a year.
    return (1.0 + annual_growth) ** (1.0 / 365.0) if annual_growth > -0.999 else 0.0


def giant_component_fraction(mean_degree: float) -> float:
    """Approximate Erdős–Rényi giant component fraction for mean degree c."""
    c = max(0.0, mean_degree)
    if c <= 1.0:
        return 0.0
    s = 0.99
    for _ in range(50):
        s = 1.0 - math.exp(-c * s)
    return float(max(0.0, min(1.0, s)))


def corrupt_committee_probability(k: int, corrupt_share: float) -> float:
    """
    Probability that a corrupt coalition controls >= 2/3 of committee.
    This is a conservative proxy for a bad result passing verification.
    """
    p = max(0.0, min(1.0, corrupt_share))
    q = math.ceil((2.0 * k) / 3.0)
    total = 0.0
    for i in range(q, k + 1):
        total += math.comb(k, i) * (p**i) * ((1 - p) ** (k - i))
    return float(total)


def ensure_out(out: str | Path) -> Path:
    p = Path(out)
    p.mkdir(parents=True, exist_ok=True)
    return p


# -----------------------------
# Model core
# -----------------------------


class DePINSim:
    def __init__(self, scenario: Scenario, seed: int = 0):
        self.s = scenario
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self._init_nodes()

    def _init_nodes(self) -> None:
        s = self.s
        gpu_idx = choose_weighted(self.rng, s.gpus, s.n_gpu_nodes)
        reg_idx = choose_weighted(self.rng, s.regions, s.n_gpu_nodes)

        gpus = np.array([s.gpus[i].name for i in gpu_idx])
        regions = np.array([s.regions[i].name for i in reg_idx])
        watt = np.array([s.gpus[i].watt for i in gpu_idx], dtype=float)
        perf = np.array([s.gpus[i].perf_units for i in gpu_idx], dtype=float)
        capex = np.array([s.gpus[i].capex_usd for i in gpu_idx], dtype=float)
        elec = np.array([s.regions[i].elec_usd_kwh for i in reg_idx], dtype=float)

        uptime = np.clip(self.rng.normal(s.uptime_mean, s.uptime_sd, size=s.n_gpu_nodes), 0.35, 0.99)
        reputation = np.clip(self.rng.normal(0.55, 0.12, size=s.n_gpu_nodes), 0.05, 0.95)
        online = self.rng.random(s.n_gpu_nodes) < 0.95

        self.node = {
            "gpu": gpus,
            "region": regions,
            "watt": watt,
            "perf": perf,
            "capex": capex,
            "elec": elec,
            "uptime": uptime,
            "reputation": reputation,
            "online": online,
            "age_days": self.rng.integers(0, 365, size=s.n_gpu_nodes),
        }
        self.treasury_usdc = s.initial_treasury_usdc
        self.credits_outstanding = s.initial_credits
        self.price = s.initial_price_usd_gpuh
        self.efficiency = 1.0
        self.sybil_fake_nodes = min(s.sybil_fake_nodes, int(s.attacker_budget_usd // max(s.stake_required_usd, 1e-9)))

    def node_hourly_cost(self) -> np.ndarray:
        s = self.s
        energy = (self.node["watt"] / 1000.0) * self.node["elec"]
        capex_hour = self.node["capex"] / max(1.0, s.capex_amort_months * 30.0 * 24.0)
        return energy + capex_hour

    def step(self, day: int) -> Dict[str, float]:
        s, rng = self.s, self.rng

        # Hardware efficiency improves over time: the same physical fleet becomes relatively less competitive
        # against new hardware unless price/reputation compensate. We model this as market-price pressure,
        # not as the old GPU getting faster.
        self.efficiency *= (1.0 + s.hw_efficiency_gain_annual) ** (1.0 / 365.0)
        competitor_ceiling = s.competitor_ceiling_usd_gpuh / self.efficiency

        # Demand with trend, random shock, and price elasticity.
        growth = daily_growth_factor(s.demand_growth_annual) ** day
        shock = max(0.05, rng.lognormal(mean=-0.5 * s.demand_vol_daily**2, sigma=s.demand_vol_daily))
        demand = s.base_daily_demand_gpuh * growth * shock * (self.price / s.initial_price_usd_gpuh) ** (-s.price_elasticity)

        # Profitability and activation.
        cost_per_gpuh = self.node_hourly_cost() / np.maximum(self.node["perf"], 1e-9)
        gross_revenue_per_gpuh = self.price * (1.0 - s.take_rate)
        margin = gross_revenue_per_gpuh - cost_per_gpuh
        stable_score = (margin - s.min_margin_for_stability_usd_gpuh) / 0.04
        active_prob = np.clip(logistic(stable_score) * self.node["uptime"] * (0.65 + 0.7 * self.node["reputation"]), 0, 0.99)
        active = (rng.random(len(active_prob)) < active_prob) & self.node["online"]

        active_nodes = int(active.sum())
        capacity_gpuh = float((active * self.node["perf"] * 24.0).sum())
        work = min(float(demand), capacity_gpuh)
        unmet = max(0.0, float(demand) - work)
        utilization = work / capacity_gpuh if capacity_gpuh > 0 else 0.0

        # Adaptive posted price: move toward target utilization, constrained by competitor ceiling.
        # If utilization > target, price rises; if utilization < target, price falls.
        price_move = 1.0 + s.adaptive_pricing_strength * (utilization - s.target_utilization)
        price_noise = rng.normal(0.0, 0.006)
        self.price = float(np.clip(self.price * price_move * (1.0 + price_noise), s.floor_price_usd_gpuh, competitor_ceiling))

        # Protocol economics: users pay credits/USDC; nodes earn internal credits; cashouts drain treasury.
        user_inflow = work * self.price
        protocol_fee = user_inflow * s.take_rate
        node_earnings_credit = user_inflow * (1.0 - s.take_rate)
        self.credits_outstanding += node_earnings_credit

        # Stress cashout rises if reserve weak or average margin negative.
        reserve_before = self.treasury_usdc / max(self.credits_outstanding, 1e-9)
        avg_margin = float(margin[active].mean()) if active_nodes else float(margin.mean())
        stress = 1.0
        if reserve_before < 1.05:
            stress *= s.stress_cashout_multiplier
        if avg_margin < 0:
            stress *= 1.5
        cashout = min(self.credits_outstanding, self.credits_outstanding * s.cashout_rate_daily * stress)
        self.credits_outstanding -= cashout
        yield_usdc = self.treasury_usdc * s.reserve_yield_apy / 365.0
        self.treasury_usdc += user_inflow - cashout + yield_usdc
        reserve_ratio = self.treasury_usdc / max(self.credits_outstanding, 1e-9)

        # Churn/onboarding. Unprofitable nodes leave faster; profitable market attracts new nodes in aggregate.
        unprofitable = margin < 0
        churn_prob = s.churn_base_daily * np.where(unprofitable, s.churn_unprofitable_multiplier, 1.0)
        churn = (rng.random(len(churn_prob)) < churn_prob) & self.node["online"]
        self.node["online"][churn] = False
        # Re-onboarding: simplified; some offline nodes come back if network is profitable.
        onboard_prob = s.onboarding_rate_daily * (1.0 + max(0.0, avg_margin) / 0.05)
        rejoin = (rng.random(len(churn_prob)) < onboard_prob) & (~self.node["online"])
        self.node["online"][rejoin] = True

        # Reputation updates.
        if active_nodes > 0:
            self.node["reputation"][active] = np.clip(self.node["reputation"][active] + 0.0015, 0.0, 1.0)
            self.node["reputation"][churn] = np.clip(self.node["reputation"][churn] - 0.01, 0.0, 1.0)

        # Sybil dynamics.
        if self.sybil_fake_nodes > 0:
            detected = rng.binomial(self.sybil_fake_nodes, s.sybil_detection_daily)
            self.sybil_fake_nodes = max(0, self.sybil_fake_nodes - detected)
        total_nodes_for_committee = active_nodes + s.n_cpu_verifiers + self.sybil_fake_nodes
        corrupt_share = self.sybil_fake_nodes / max(total_nodes_for_committee, 1)
        pass_bad_prob_if_sampled = corrupt_committee_probability(s.verifier_committee_k, corrupt_share)
        verification_detection_prob = s.verify_sampling_rate * (1.0 - pass_bad_prob_if_sampled)
        bad_results = work * s.lazy_worker_rate
        undetected_bad = bad_results * (1.0 - verification_detection_prob)
        expected_slashing = bad_results * verification_detection_prob * s.slashing_loss_usd

        # P2P overlay metrics.
        total_p2p_nodes = active_nodes + s.n_cpu_verifiers
        relay_fraction = 1.0 - s.direct_connection_success
        avg_rtt = s.direct_connection_success * s.direct_rtt_ms + relay_fraction * s.relay_rtt_ms
        mean_degree = min(max(0.0, s.gossip_degree), max(total_p2p_nodes - 1, 0))
        giant = giant_component_fraction(mean_degree) if total_p2p_nodes > 2 else 0.0
        hops = math.log(max(total_p2p_nodes, 2), max(mean_degree, 1.0001)) if mean_degree > 1 else float("inf")
        gossip_latency_ms = avg_rtt * hops * s.gossip_overhead_factor if math.isfinite(hops) else 1e9
        msg_count = work * s.receipts_per_gpuh
        gossip_mb_day = msg_count * s.avg_msg_size_bytes * max(mean_degree, 1.0) / 1_000_000.0

        return {
            "seed": self.seed,
            "day": day,
            "price_usd_gpuh": self.price,
            "competitor_ceiling_usd_gpuh": competitor_ceiling,
            "demand_gpuh": demand,
            "work_gpuh": work,
            "unmet_gpuh": unmet,
            "fill_rate": work / max(demand, 1e-9),
            "active_gpu_nodes": active_nodes,
            "online_gpu_nodes": int(self.node["online"].sum()),
            "capacity_gpuh": capacity_gpuh,
            "utilization": utilization,
            "avg_margin_usd_gpuh": avg_margin,
            "treasury_usdc": self.treasury_usdc,
            "credits_outstanding": self.credits_outstanding,
            "reserve_ratio": reserve_ratio,
            "user_inflow_usdc": user_inflow,
            "protocol_fee_usdc": protocol_fee,
            "node_earnings_credit": node_earnings_credit,
            "cashout_usdc": cashout,
            "expected_slashing_usd": expected_slashing,
            "sybil_fake_nodes": self.sybil_fake_nodes,
            "corrupt_committee_probability": pass_bad_prob_if_sampled,
            "verification_detection_probability": verification_detection_prob,
            "bad_results_gpuh_equiv": bad_results,
            "undetected_bad_gpuh_equiv": undetected_bad,
            "p2p_nodes": total_p2p_nodes,
            "giant_component_fraction": giant,
            "gossip_latency_ms": gossip_latency_ms,
            "gossip_traffic_mb_day": gossip_mb_day,
            "relay_fraction": relay_fraction,
        }

    def run(self, days: int | None = None) -> pd.DataFrame:
        n = self.s.days if days is None else days
        rows = [self.step(day) for day in range(n)]
        return pd.DataFrame(rows)

    def node_region_table(self) -> pd.DataFrame:
        df = pd.DataFrame({
            "gpu": self.node["gpu"],
            "region": self.node["region"],
            "watt": self.node["watt"],
            "perf": self.node["perf"],
            "elec_usd_kwh": self.node["elec"],
            "capex_usd": self.node["capex"],
            "hourly_cost_usd": self.node_hourly_cost(),
        })
        return (
            df.groupby(["region", "gpu"], as_index=False)
            .agg(
                nodes=("gpu", "size"),
                avg_watt=("watt", "mean"),
                avg_perf=("perf", "mean"),
                avg_hourly_cost=("hourly_cost_usd", "mean"),
                elec_usd_kwh=("elec_usd_kwh", "mean"),
            )
            .sort_values(["region", "gpu"])
        )


# -----------------------------
# Metrics and plots
# -----------------------------


def summarize_run(df: pd.DataFrame, scenario: str, seed: int) -> Dict[str, float | str | int]:
    last = df.iloc[-1]
    weak_reserve_days = int((df["reserve_ratio"] < 1.0).sum())
    severe_reserve_days = int((df["reserve_ratio"] < 0.75).sum())
    bad_share = df["undetected_bad_gpuh_equiv"].sum() / max(df["work_gpuh"].sum(), 1e-9)
    revenue = df["protocol_fee_usdc"].sum()
    result = {
        "scenario": scenario,
        "seed": seed,
        "days": int(df["day"].max() + 1),
        "avg_fill_rate": float(df["fill_rate"].mean()),
        "p10_fill_rate": float(df["fill_rate"].quantile(0.10)),
        "avg_utilization": float(df["utilization"].mean()),
        "avg_price_usd_gpuh": float(df["price_usd_gpuh"].mean()),
        "final_price_usd_gpuh": float(last["price_usd_gpuh"]),
        "avg_active_gpu_nodes": float(df["active_gpu_nodes"].mean()),
        "final_online_gpu_nodes": int(last["online_gpu_nodes"]),
        "min_reserve_ratio": float(df["reserve_ratio"].min()),
        "final_reserve_ratio": float(last["reserve_ratio"]),
        "weak_reserve_days": weak_reserve_days,
        "severe_reserve_days": severe_reserve_days,
        "final_treasury_usdc": float(last["treasury_usdc"]),
        "protocol_revenue_usdc": float(revenue),
        "avg_margin_usd_gpuh": float(df["avg_margin_usd_gpuh"].mean()),
        "avg_gossip_latency_ms": float(df["gossip_latency_ms"].replace(1e9, np.nan).mean()),
        "min_giant_component_fraction": float(df["giant_component_fraction"].min()),
        "avg_verification_detection_probability": float(df["verification_detection_probability"].mean()),
        "undetected_bad_share": float(bad_share),
        "final_sybil_fake_nodes": int(last["sybil_fake_nodes"]),
    }
    result["spiral_flag"] = int(
        (result["min_reserve_ratio"] < 0.75)
        or (result["avg_fill_rate"] < 0.55)
        or (result["final_online_gpu_nodes"] < 0.45 * df["online_gpu_nodes"].iloc[0])
    )
    return result


def write_plots(ts: pd.DataFrame, summary: pd.DataFrame, out: Path) -> None:
    if plt is None:
        print("matplotlib unavailable; skipping plots")
        return
    # Median/IQR per day across runs.
    metrics = [
        ("fill_rate", "Fill rate"),
        ("reserve_ratio", "Reserve ratio"),
        ("price_usd_gpuh", "Price USD / GPU-hour"),
        ("active_gpu_nodes", "Active GPU nodes"),
        ("gossip_latency_ms", "Gossip latency ms"),
        ("undetected_bad_gpuh_equiv", "Undetected bad work GPUh-equiv/day"),
    ]
    grouped = ts.groupby("day")
    for col, title in metrics:
        q = grouped[col].quantile([0.25, 0.5, 0.75]).unstack()
        fig = plt.figure(figsize=(10, 5))
        ax = fig.add_subplot(111)
        ax.plot(q.index, q[0.5], label="median")
        ax.fill_between(q.index, q[0.25], q[0.75], alpha=0.25, label="IQR")
        ax.set_title(title)
        ax.set_xlabel("day")
        ax.set_ylabel(col)
        ax.legend()
        fig.tight_layout()
        fig.savefig(out / f"{col}.png", dpi=150)
        plt.close(fig)

    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_subplot(111)
    ax.hist(summary["min_reserve_ratio"], bins=30)
    ax.set_title("Distribution of minimum reserve ratio")
    ax.set_xlabel("min reserve ratio")
    ax.set_ylabel("runs")
    fig.tight_layout()
    fig.savefig(out / "min_reserve_ratio_hist.png", dpi=150)
    plt.close(fig)


def run_monte_carlo(s: Scenario, runs: int, days: int, out: Path, plots: bool, export_node_regions: bool) -> Tuple[pd.DataFrame, pd.DataFrame]:
    all_ts: List[pd.DataFrame] = []
    summaries: List[Dict] = []
    node_tables: List[pd.DataFrame] = []

    for i in range(runs):
        sim = DePINSim(scenario=s, seed=i)
        if export_node_regions and i == 0:
            node_tables.append(sim.node_region_table())
        df = sim.run(days)
        all_ts.append(df)
        summaries.append(summarize_run(df, s.name, i))

    ts = pd.concat(all_ts, ignore_index=True)
    summary = pd.DataFrame(summaries)

    ts.to_csv(out / "timeseries.csv", index=False)
    summary.to_csv(out / "summary.csv", index=False)
    with open(out / "scenario.json", "w", encoding="utf-8") as f:
        json.dump(asdict(s), f, indent=2, ensure_ascii=False, default=lambda o: asdict(o))
    if node_tables:
        node_tables[0].to_csv(out / "node_region_mix.csv", index=False)
    if plots:
        write_plots(ts, summary, out)
    return ts, summary


def print_console_report(summary: pd.DataFrame) -> None:
    def pct(x: float) -> str:
        return f"{100*x:.1f}%"

    fields = {
        "avg_fill_rate": "avg fill",
        "p10_fill_rate": "p10 fill",
        "avg_utilization": "avg util",
        "min_reserve_ratio": "min reserve",
        "final_reserve_ratio": "final reserve",
        "protocol_revenue_usdc": "protocol rev",
        "avg_margin_usd_gpuh": "avg node margin/GPUh",
        "avg_gossip_latency_ms": "avg gossip ms",
        "undetected_bad_share": "bad share",
    }
    print("\nMonte Carlo summary")
    print("-------------------")
    print(f"runs: {len(summary)}")
    print(f"spiral flags: {int(summary['spiral_flag'].sum())}/{len(summary)} ({pct(summary['spiral_flag'].mean())})")
    for col, label in fields.items():
        med = summary[col].median()
        p10 = summary[col].quantile(0.10)
        p90 = summary[col].quantile(0.90)
        if "rate" in col or "share" in col or "util" in col:
            print(f"{label:24s} median={pct(med):>8s} p10={pct(p10):>8s} p90={pct(p90):>8s}")
        else:
            print(f"{label:24s} median={med:10.4f} p10={p10:10.4f} p90={p90:10.4f}")


# -----------------------------
# CLI
# -----------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DePIN GPU compute network Monte Carlo simulator")
    p.add_argument("--scenario", choices=["bear", "base", "bull", "stress", "security"], default="base")
    p.add_argument("--runs", type=int, default=50)
    p.add_argument("--days", type=int, default=365)
    p.add_argument("--out", type=str, default="sim_out")
    p.add_argument("--plots", action="store_true")
    p.add_argument("--export-node-regions", action="store_true")

    # Useful overrides without editing code.
    p.add_argument("--gpu-nodes", type=int, default=None)
    p.add_argument("--cpu-verifiers", type=int, default=None)
    p.add_argument("--price", type=float, default=None, help="Initial USD per normalized GPU-hour")
    p.add_argument("--take-rate", type=float, default=None)
    p.add_argument("--committee-k", type=int, default=None)
    p.add_argument("--sampling-rate", type=float, default=None)
    p.add_argument("--sybil-fake-nodes", type=int, default=None)
    p.add_argument("--stake", type=float, default=None, help="Stake required per node, USD")
    return p.parse_args()


def apply_overrides(s: Scenario, args: argparse.Namespace) -> Scenario:
    s.days = args.days
    if args.gpu_nodes is not None:
        s.n_gpu_nodes = args.gpu_nodes
    if args.cpu_verifiers is not None:
        s.n_cpu_verifiers = args.cpu_verifiers
    if args.price is not None:
        s.initial_price_usd_gpuh = args.price
    if args.take_rate is not None:
        s.take_rate = args.take_rate
    if args.committee_k is not None:
        s.verifier_committee_k = args.committee_k
    if args.sampling_rate is not None:
        s.verify_sampling_rate = args.sampling_rate
    if args.sybil_fake_nodes is not None:
        s.sybil_fake_nodes = args.sybil_fake_nodes
    if args.stake is not None:
        s.stake_required_usd = args.stake
    return s


def main() -> int:
    args = parse_args()
    out = ensure_out(args.out)
    s = apply_overrides(scenario_preset(args.scenario), args)
    ts, summary = run_monte_carlo(s, runs=args.runs, days=args.days, out=out, plots=args.plots, export_node_regions=args.export_node_regions)
    print_console_report(summary)
    print(f"\nWrote: {out / 'timeseries.csv'}")
    print(f"Wrote: {out / 'summary.csv'}")
    if args.plots:
        print(f"Wrote plots to: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
