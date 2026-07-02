# AGENTS.md — crate `proto`

Scoped rules for the wire-format / receipt crate. These **add to** the root
`AGENTS.md`; on conflict, the stricter rule wins. Codex applies the closest
`AGENTS.md` to each changed file, so put extra scrutiny here.

## Purpose

`proto` defines every type that crosses the network or gets hashed into a
commitment: `ComputeReceipt`, `JobManifest`, `GossipMsg`, and the ID newtypes.
It is the trust root of the protocol — a bug here is a protocol-wide bug.

## Hard constraints

- **`#![no_std]`-compatible** where feasible; this crate may run inside the
  WASM guest. No `std`-only dependencies without an ADR.
- **postcard is the only wire encoding.** Do not add serde_json, bincode, or
  protobuf to this crate. Encoding must be deterministic and reproducible.
- **Canonical byte layout.** Field order is part of the wire contract. Adding,
  removing, or reordering a field in any `*Receipt`/`*Msg` type is a
  **breaking protocol change** and requires an ADR + explicit human approval,
  plus a version bump on the message envelope.
- **No non-determinism.** No `HashMap` (use `BTreeMap`), no floats in hashed
  structures, no timestamps used as anything but advisory (never in a hash that
  a verifier must reproduce), no `SystemtimeUUID`/random IDs — IDs are BLAKE3 of
  canonical bytes.
- **Signatures cover all semantic fields.** If you add a field that changes
  meaning, it MUST be inside the signed byte range. Document the signed range.

## Required tests (P1 if missing, P0 if the type is security-relevant)

- `proptest` round-trip: `decode(encode(x)) == x` for every public wire type.
- A signature verification test with a known-good and a tampered payload.
- A "canonical bytes are stable" test: encoding a fixed fixture yields fixed
  bytes (guards against accidental layout changes).

## Review focus for `@codex review` here

- Does any new field escape the signed range? → **P0**.
- Any `HashMap`, float, or wall-clock in a hashed/committed struct? → **P0**.
- Field reorder/removal without ADR + envelope version bump? → **P0**.
- Missing round-trip or canonical-bytes test? → **P1**.
