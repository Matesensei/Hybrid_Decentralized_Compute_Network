#![forbid(unsafe_code)]

use core::fmt;
use serde::{Deserialize, Serialize};

/// A 32-byte protocol commitment.
pub type Commitment = [u8; 32];

/// Settlement chain family. This enum is descriptive, not a priority order.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ChainNamespace {
    /// EVM-compatible chains such as Base, Ethereum, BNB, and Avalanche C-Chain.
    Evm,
    /// Solana settlement adapters.
    Solana,
    /// Sui settlement adapters.
    Sui,
    /// Polkadot/Substrate settlement adapters.
    Polkadot,
    /// XRP Ledger settlement adapters.
    Xrpl,
    /// Future chain families that do not fit an existing namespace.
    Custom(String),
}

/// Chain identifier used by settlement adapters.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct ChainId {
    /// Chain family.
    pub namespace: ChainNamespace,
    /// Human-readable chain reference, for example "base-sepolia".
    pub reference: String,
}

impl ChainId {
    /// Creates a new chain identifier.
    pub fn new(namespace: ChainNamespace, reference: impl Into<String>) -> Self {
        Self {
            namespace,
            reference: reference.into(),
        }
    }
}

/// Opaque account address bytes. Concrete adapters own chain-specific parsing.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct AccountId {
    /// Address bytes in the adapter's canonical representation.
    pub bytes: Vec<u8>,
}

impl AccountId {
    /// Creates an account identifier from canonical bytes.
    pub fn new(bytes: Vec<u8>) -> Self {
        Self { bytes }
    }
}

/// Asset identifier in integer base units.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct AssetId {
    /// Chain where the asset is settled.
    pub chain: ChainId,
    /// Symbol for display and logs only.
    pub symbol: String,
    /// Number of decimal places used by the token contract or ledger.
    pub decimals: u8,
    /// Optional issuer or contract bytes in adapter canonical form.
    pub issuer: Option<Vec<u8>>,
}

/// Amount in integer base units. Money is never represented with floats.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Amount {
    /// Asset being transferred.
    pub asset: AssetId,
    /// Integer base-unit amount.
    pub units: u128,
}

impl Amount {
    /// Creates an amount in base units.
    pub fn new(asset: AssetId, units: u128) -> Self {
        Self { asset, units }
    }

    /// Adds two amounts with the same asset, checking overflow.
    pub fn checked_add_same_asset(&self, rhs: &Self) -> Result<Self, SettlementError> {
        if self.asset != rhs.asset {
            return Err(SettlementError::AssetMismatch);
        }
        let units = self
            .units
            .checked_add(rhs.units)
            .ok_or(SettlementError::AmountOverflow)?;
        Ok(Self {
            asset: self.asset.clone(),
            units,
        })
    }

    /// Subtracts two amounts with the same asset, checking underflow.
    pub fn checked_sub_same_asset(&self, rhs: &Self) -> Result<Self, SettlementError> {
        if self.asset != rhs.asset {
            return Err(SettlementError::AssetMismatch);
        }
        let units = self
            .units
            .checked_sub(rhs.units)
            .ok_or(SettlementError::AmountUnderflow)?;
        Ok(Self {
            asset: self.asset.clone(),
            units,
        })
    }
}

/// Explicit release condition for a non-custodial compute escrow.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReleaseCondition {
    /// Release after a verifier quorum accepts the receipt commitment.
    ReceiptQuorum {
        /// Commitment to accepted receipt body or batch.
        receipt_commit: Commitment,
        /// Required acceptance threshold.
        threshold: u16,
        /// Total verifier committee size.
        committee_size: u16,
    },
    /// Release when the preimage for this hash is revealed.
    Hashlock {
        /// Hash of the accepted preimage.
        preimage_hash: Commitment,
    },
}

/// Request to create a chain-local escrow.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EscrowCreate {
    /// Payer account on the settlement chain.
    pub payer: AccountId,
    /// Worker account on the settlement chain.
    pub worker: AccountId,
    /// Integer amount locked by the escrow.
    pub amount: Amount,
    /// Compute job commitment.
    pub job_id: Commitment,
    /// Epoch after which refund may be attempted by the adapter.
    pub cancel_after_epoch: u64,
    /// Explicit release condition.
    pub release_condition: ReleaseCondition,
    /// Caller-supplied nonce used for replay protection.
    pub nonce: Commitment,
}

impl EscrowCreate {
    /// Validates chain-neutral escrow invariants before adapter submission.
    pub fn validate(&self) -> Result<(), SettlementError> {
        if self.amount.units == 0 {
            return Err(SettlementError::ZeroAmount);
        }
        validate_release_condition(&self.release_condition)
    }
}

/// Chain-local escrow handle returned by an adapter.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EscrowHandle {
    /// Settlement chain that owns this escrow.
    pub chain: ChainId,
    /// Opaque chain-local escrow identifier.
    pub escrow_id: Vec<u8>,
    /// Nonce copied from the create request for replay-safe retries.
    pub nonce: Commitment,
}

/// Proof supplied to release an escrow.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReleaseProof {
    /// Condition being satisfied.
    pub condition: ReleaseCondition,
    /// Opaque adapter-specific proof bytes.
    pub proof_bytes: Vec<u8>,
    /// Receipt identifiers included in the proof.
    pub receipt_ids: Vec<Commitment>,
}

/// Opaque transaction identifier returned by an adapter.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TxId {
    /// Transaction bytes or canonical string bytes.
    pub bytes: Vec<u8>,
}

/// Finality status for a settlement transaction.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FinalityStatus {
    /// The transaction was submitted but is not final.
    Pending,
    /// The transaction reached the adapter's configured finality threshold.
    Finalized,
    /// The transaction failed or was reverted.
    Failed,
}

/// Chain-neutral settlement adapter contract.
pub trait SettlementAdapter {
    /// Returns the chain handled by this adapter.
    fn chain_id(&self) -> &ChainId;

    /// Creates a non-custodial escrow on the adapter's chain.
    fn escrow_create(&self, request: &EscrowCreate) -> Result<EscrowHandle, SettlementError>;

    /// Releases an escrow only after the release proof satisfies the condition.
    fn escrow_release(
        &self,
        handle: &EscrowHandle,
        proof: &ReleaseProof,
    ) -> Result<TxId, SettlementError>;

    /// Refunds an escrow after the adapter-specific cancellation condition.
    fn escrow_refund(&self, handle: &EscrowHandle) -> Result<TxId, SettlementError>;

    /// Checks finality for a previously submitted transaction.
    fn finality_status(&self, tx: &TxId) -> Result<FinalityStatus, SettlementError>;
}

/// Errors returned by chain-neutral settlement validation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SettlementError {
    /// Amount was zero.
    ZeroAmount,
    /// Arithmetic overflow on an amount.
    AmountOverflow,
    /// Arithmetic underflow on an amount.
    AmountUnderflow,
    /// Arithmetic attempted across different assets.
    AssetMismatch,
    /// Receipt quorum threshold was invalid.
    InvalidQuorum,
    /// A release condition had an all-zero commitment.
    EmptyCommitment,
    /// Adapter rejected a request.
    AdapterRejected(String),
}

impl fmt::Display for SettlementError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ZeroAmount => f.write_str("settlement amount must be non-zero"),
            Self::AmountOverflow => f.write_str("settlement amount overflow"),
            Self::AmountUnderflow => f.write_str("settlement amount underflow"),
            Self::AssetMismatch => f.write_str("settlement asset mismatch"),
            Self::InvalidQuorum => f.write_str("invalid receipt quorum"),
            Self::EmptyCommitment => f.write_str("release commitment must not be all zero"),
            Self::AdapterRejected(reason) => write!(f, "adapter rejected request: {reason}"),
        }
    }
}

impl std::error::Error for SettlementError {}

/// Validates release conditions without knowing any concrete settlement chain.
pub fn validate_release_condition(condition: &ReleaseCondition) -> Result<(), SettlementError> {
    match condition {
        ReleaseCondition::ReceiptQuorum {
            receipt_commit,
            threshold,
            committee_size,
        } => {
            if is_zero_commitment(receipt_commit) {
                return Err(SettlementError::EmptyCommitment);
            }
            if *threshold == 0 || *committee_size == 0 || threshold > committee_size {
                return Err(SettlementError::InvalidQuorum);
            }
            Ok(())
        }
        ReleaseCondition::Hashlock { preimage_hash } => {
            if is_zero_commitment(preimage_hash) {
                return Err(SettlementError::EmptyCommitment);
            }
            Ok(())
        }
    }
}

fn is_zero_commitment(commitment: &Commitment) -> bool {
    commitment.iter().all(|byte| *byte == 0)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn chain(reference: &str) -> ChainId {
        ChainId::new(ChainNamespace::Evm, reference)
    }

    fn asset(reference: &str) -> AssetId {
        AssetId {
            chain: chain(reference),
            symbol: "USDC".to_owned(),
            decimals: 6,
            issuer: None,
        }
    }

    fn account(byte: u8) -> AccountId {
        AccountId::new(vec![byte; 20])
    }

    fn release_condition() -> ReleaseCondition {
        ReleaseCondition::ReceiptQuorum {
            receipt_commit: [9; 32],
            threshold: 2,
            committee_size: 3,
        }
    }

    #[test]
    fn amount_arithmetic_rejects_asset_mismatch() {
        let base = Amount::new(asset("base-sepolia"), 100);
        let sui = Amount::new(asset("sui-testnet"), 100);
        assert_eq!(
            base.checked_add_same_asset(&sui),
            Err(SettlementError::AssetMismatch)
        );
    }

    #[test]
    fn amount_arithmetic_checks_overflow_and_underflow() {
        let asset = asset("base-sepolia");
        let max = Amount::new(asset.clone(), u128::MAX);
        let one = Amount::new(asset.clone(), 1);
        assert_eq!(
            max.checked_add_same_asset(&one),
            Err(SettlementError::AmountOverflow)
        );
        assert_eq!(
            one.checked_sub_same_asset(&Amount::new(asset, 2)),
            Err(SettlementError::AmountUnderflow)
        );
    }

    #[test]
    fn release_condition_rejects_invalid_quorum() {
        let condition = ReleaseCondition::ReceiptQuorum {
            receipt_commit: [1; 32],
            threshold: 4,
            committee_size: 3,
        };
        assert_eq!(
            validate_release_condition(&condition),
            Err(SettlementError::InvalidQuorum)
        );
    }

    #[test]
    fn release_condition_rejects_empty_commitment() {
        let condition = ReleaseCondition::Hashlock {
            preimage_hash: [0; 32],
        };
        assert_eq!(
            validate_release_condition(&condition),
            Err(SettlementError::EmptyCommitment)
        );
    }

    #[test]
    fn escrow_create_validation_is_chain_neutral() {
        let request = EscrowCreate {
            payer: account(1),
            worker: account(2),
            amount: Amount::new(asset("base-sepolia"), 1_000_000),
            job_id: [3; 32],
            cancel_after_epoch: 100,
            release_condition: release_condition(),
            nonce: [4; 32],
        };
        assert_eq!(request.validate(), Ok(()));
    }
}
