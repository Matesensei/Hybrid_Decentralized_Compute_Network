#![no_std]
#![forbid(unsafe_code)]

extern crate alloc;

use alloc::vec::Vec;
use core::fmt;
use serde::{Deserialize, Serialize};

/// Current schema version for all first-sprint wire messages.
pub const SCHEMA_VERSION: u16 = 1;

/// Expected byte length for Ed25519 signatures.
pub const ED25519_SIGNATURE_LEN: usize = 64;

/// A BLAKE3 digest used as a protocol commitment.
pub type Hash32 = [u8; 32];

/// Canonical node identity bytes.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct NodeId(pub Hash32);

/// Canonical job identifier, derived from a `JobManifest`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct JobId(pub Hash32);

/// Canonical compute receipt identifier, derived from signed receipt body bytes.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct ReceiptId(pub Hash32);

/// Deterministic workload classes supported by the first protocol envelope.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorkloadKind {
    /// Fuel-metered WASM/WASI task with deterministic replay.
    WasmDeterministic,
    /// Tile-render task where output verification is a content hash comparison.
    RenderTile,
    /// Research-only GPU inference path. This is not accepted for settlement yet.
    GpuInferenceExperimental,
    /// FlowMate distributed backtest task with deterministic input snapshots.
    FlowMateBacktest,
}

/// Execution environment reported by a worker.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutorKind {
    /// CPU-only deterministic runtime.
    CpuWasm,
    /// Hybrid CPU plus GPU worker. Verification rules are workload-specific.
    HybridGpuCpu,
}

/// Verification proof strategy carried by a receipt.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProofKind {
    /// A verifier can re-run the task and compare the output commitment.
    DeterministicReplay,
    /// Multiple workers ran the same task and reached a quorum on the output.
    RedundantExecution,
}

/// Work request metadata committed before any worker executes a task.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct JobManifest {
    /// Wire schema version.
    pub schema_version: u16,
    /// Workload category.
    pub workload: WorkloadKind,
    /// Content-addressed input bundle commitment.
    pub input_commit: Hash32,
    /// Maximum deterministic fuel units allowed for execution.
    pub max_fuel: u64,
    /// Operator-defined nonce preventing accidental duplicate job IDs.
    pub nonce: Hash32,
}

impl JobManifest {
    /// Builds a manifest using the current schema version.
    pub fn new(workload: WorkloadKind, input_commit: Hash32, max_fuel: u64, nonce: Hash32) -> Self {
        Self {
            schema_version: SCHEMA_VERSION,
            workload,
            input_commit,
            max_fuel,
            nonce,
        }
    }

    /// Derives the canonical job ID from postcard-encoded manifest bytes.
    pub fn job_id(&self) -> Result<JobId, ProtoError> {
        Ok(JobId(hash_canonical(self)?))
    }
}

/// Integer execution metrics that can safely enter signed receipt bytes.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExecutionMetrics {
    /// Fuel units consumed by deterministic execution.
    pub fuel_consumed: u64,
    /// Peak memory observed by the sandbox, in bytes.
    pub peak_memory_bytes: u64,
    /// Billable compute units after the workload adapter applies its policy.
    pub billable_units: u64,
}

/// Compact proof metadata committed by a worker.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProofBundle {
    /// Verification strategy.
    pub kind: ProofKind,
    /// Commitment to the proof witness or verifier transcript.
    pub witness_commit: Hash32,
    /// Verifier committee size used for this result.
    pub committee_size: u16,
    /// Quorum required for acceptance.
    pub quorum: u16,
}

/// Semantic body of a receipt. The signature covers this structure exactly.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReceiptBody {
    /// Wire schema version.
    pub schema_version: u16,
    /// Job being claimed.
    pub job_id: JobId,
    /// Worker identity.
    pub worker: NodeId,
    /// Runtime class that produced the output commitment.
    pub executor: ExecutorKind,
    /// Input bundle commitment observed by the worker.
    pub input_commit: Hash32,
    /// Output bundle commitment produced by the worker.
    pub output_commit: Hash32,
    /// Deterministic billing and resource metrics.
    pub metrics: ExecutionMetrics,
    /// Verification proof metadata.
    pub proof: ProofBundle,
}

impl ReceiptBody {
    /// Builds a receipt body using the current schema version.
    pub fn new(
        job_id: JobId,
        worker: NodeId,
        executor: ExecutorKind,
        input_commit: Hash32,
        output_commit: Hash32,
        metrics: ExecutionMetrics,
        proof: ProofBundle,
    ) -> Self {
        Self {
            schema_version: SCHEMA_VERSION,
            job_id,
            worker,
            executor,
            input_commit,
            output_commit,
            metrics,
            proof,
        }
    }
}

/// Signed compute receipt broadcast by a worker.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ComputeReceipt {
    /// The exact semantic body that is signed.
    pub body: ReceiptBody,
    /// Ed25519 signature bytes over `signing_payload(body)`.
    pub signature: Vec<u8>,
}

impl ComputeReceipt {
    /// Builds a receipt and validates signature byte length.
    pub fn new(body: ReceiptBody, signature: Vec<u8>) -> Result<Self, ProtoError> {
        if signature.len() != ED25519_SIGNATURE_LEN {
            return Err(ProtoError::InvalidSignatureLength {
                actual: signature.len(),
            });
        }
        Ok(Self { body, signature })
    }

    /// Returns the canonical bytes that must be signed and verified.
    pub fn signing_payload(&self) -> Result<Vec<u8>, ProtoError> {
        to_canonical_bytes(&self.body)
    }

    /// Derives the receipt ID from the signed body, excluding the signature.
    pub fn receipt_id(&self) -> Result<ReceiptId, ProtoError> {
        Ok(ReceiptId(hash_canonical(&self.body)?))
    }
}

/// Errors produced by protocol encoding and invariant checks.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProtoError {
    /// Canonical postcard encoding failed.
    Encode,
    /// Canonical postcard decoding failed.
    Decode,
    /// Signature length was not the expected Ed25519 size.
    InvalidSignatureLength {
        /// Actual byte length supplied.
        actual: usize,
    },
}

impl fmt::Display for ProtoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Encode => f.write_str("canonical protocol encoding failed"),
            Self::Decode => f.write_str("canonical protocol decoding failed"),
            Self::InvalidSignatureLength { actual } => {
                write!(f, "invalid Ed25519 signature length: {actual}")
            }
        }
    }
}

/// Encodes a value with the protocol's canonical postcard format.
pub fn to_canonical_bytes<T: Serialize + ?Sized>(value: &T) -> Result<Vec<u8>, ProtoError> {
    postcard::to_allocvec(value).map_err(|_| ProtoError::Encode)
}

/// Decodes a value from the protocol's canonical postcard format.
pub fn from_canonical_bytes<'a, T: Deserialize<'a>>(bytes: &'a [u8]) -> Result<T, ProtoError> {
    postcard::from_bytes(bytes).map_err(|_| ProtoError::Decode)
}

/// Hashes the canonical byte representation of a value with BLAKE3.
pub fn hash_canonical<T: Serialize + ?Sized>(value: &T) -> Result<Hash32, ProtoError> {
    let bytes = to_canonical_bytes(value)?;
    Ok(*blake3::hash(&bytes).as_bytes())
}

#[cfg(test)]
extern crate std;

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    fn fixture_hash(byte: u8) -> Hash32 {
        [byte; 32]
    }

    fn fixture_receipt() -> ComputeReceipt {
        let manifest = JobManifest::new(
            WorkloadKind::FlowMateBacktest,
            fixture_hash(1),
            10_000,
            fixture_hash(2),
        );
        let body = ReceiptBody::new(
            manifest.job_id().unwrap(),
            NodeId(fixture_hash(3)),
            ExecutorKind::CpuWasm,
            fixture_hash(1),
            fixture_hash(4),
            ExecutionMetrics {
                fuel_consumed: 9_100,
                peak_memory_bytes: 64 * 1024 * 1024,
                billable_units: 42,
            },
            ProofBundle {
                kind: ProofKind::DeterministicReplay,
                witness_commit: fixture_hash(5),
                committee_size: 3,
                quorum: 2,
            },
        );
        ComputeReceipt::new(body, alloc::vec![7; ED25519_SIGNATURE_LEN]).unwrap()
    }

    #[test]
    fn receipt_id_ignores_signature_bytes() {
        let mut receipt = fixture_receipt();
        let before = receipt.receipt_id().unwrap();
        receipt.signature[0] = 8;
        let after = receipt.receipt_id().unwrap();
        assert_eq!(before, after);
    }

    #[test]
    fn invalid_signature_length_is_rejected() {
        let body = fixture_receipt().body;
        assert_eq!(
            ComputeReceipt::new(body, alloc::vec![1; 63]),
            Err(ProtoError::InvalidSignatureLength { actual: 63 })
        );
    }

    #[test]
    fn fixed_fixture_has_stable_canonical_bytes() {
        let bytes = to_canonical_bytes(&fixture_receipt()).unwrap();
        let digest = *blake3::hash(&bytes).as_bytes();
        assert_eq!(bytes.len(), 237);
        assert_eq!(
            digest,
            [
                160, 3, 147, 39, 11, 78, 103, 89, 12, 208, 155, 47, 237, 119, 164, 26, 95, 54, 104,
                148, 102, 81, 122, 20, 251, 160, 88, 188, 23, 37, 136, 250
            ]
        );
    }

    proptest! {
        #[test]
        fn job_manifest_round_trips(
            input_commit in any::<Hash32>(),
            nonce in any::<Hash32>(),
            max_fuel in any::<u64>(),
        ) {
            let manifest = JobManifest::new(
                WorkloadKind::WasmDeterministic,
                input_commit,
                max_fuel,
                nonce,
            );
            let bytes = to_canonical_bytes(&manifest).unwrap();
            let decoded: JobManifest = from_canonical_bytes(&bytes).unwrap();
            prop_assert_eq!(decoded, manifest);
        }

        #[test]
        fn receipt_round_trips(
            job_id in any::<Hash32>(),
            worker in any::<Hash32>(),
            input_commit in any::<Hash32>(),
            output_commit in any::<Hash32>(),
            witness_commit in any::<Hash32>(),
            fuel_consumed in any::<u64>(),
            peak_memory_bytes in any::<u64>(),
            billable_units in any::<u64>(),
        ) {
            let body = ReceiptBody::new(
                JobId(job_id),
                NodeId(worker),
                ExecutorKind::CpuWasm,
                input_commit,
                output_commit,
                ExecutionMetrics {
                    fuel_consumed,
                    peak_memory_bytes,
                    billable_units,
                },
                ProofBundle {
                    kind: ProofKind::DeterministicReplay,
                    witness_commit,
                    committee_size: 3,
                    quorum: 2,
                },
            );
            let receipt = ComputeReceipt::new(body, alloc::vec![9; ED25519_SIGNATURE_LEN]).unwrap();
            let bytes = to_canonical_bytes(&receipt).unwrap();
            let decoded: ComputeReceipt = from_canonical_bytes(&bytes).unwrap();
            prop_assert_eq!(decoded, receipt);
        }
    }
}
