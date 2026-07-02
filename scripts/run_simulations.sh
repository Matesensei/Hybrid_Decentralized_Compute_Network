#!/usr/bin/env bash
set -euo pipefail

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/matplotlib}"

python sim/depin_network_model.py --scenario base --runs 50 --days 365 --plots --export-node-regions --out out/base
python sim/depin_network_model.py --scenario stress --runs 100 --days 365 --plots --out out/stress
python sim/depin_network_model.py --scenario security --runs 100 --days 365 --plots --out out/security
