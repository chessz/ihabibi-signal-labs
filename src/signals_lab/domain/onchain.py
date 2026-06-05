"""
On-chain domain models for signals-lab
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

from .enums import ObservationType

if TYPE_CHECKING:
    from .market import AssetPair


class OnChainObservation(BaseModel):
    """Raw on-chain data observation (time-series)"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset_pair: "AssetPair"
    timestamp: datetime
    exchange_inflow_usd: Decimal = Field(default=Decimal("0"), ge=0)
    exchange_outflow_usd: Decimal = Field(default=Decimal("0"), ge=0)
    whale_transaction_count: int = Field(default=0, ge=0)
    whale_transaction_volume_usd: Decimal = Field(default=Decimal("0"), ge=0)
    stablecoin_minted_usd: Decimal = Field(default=Decimal("0"), ge=0)
    stablecoin_redeemed_usd: Decimal = Field(default=Decimal("0"), ge=0)
    supply_on_exchanges_pct: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        description="% of total supply on exchanges"
    )
    large_holder_net_flow_usd: Decimal = Field(default=Decimal("0"))
    active_addresses: Optional[int] = None
    transaction_count: Optional[int] = None
    hash_rate: Optional[Decimal] = None  # For PoW chains
    staking_ratio: Optional[Decimal] = None  # For PoS chains
    source: str = Field(..., description="Data provider identifier")

    @property
    def net_exchange_flow_usd(self) -> Decimal:
        """Positive = outflow (accumulation), Negative = inflow (selling pressure)"""
        return self.exchange_outflow_usd - self.exchange_inflow_usd

    @property
    def net_stablecoin_flow_usd(self) -> Decimal:
        return self.stablecoin_minted_usd - self.stablecoin_redeemed_usd

    @property
    def flow_imbalance_ratio(self) -> Optional[Decimal]:
        """Ratio of outflow to inflow (>1 means more outflow/accumulation)"""
        if self.exchange_inflow_usd == 0:
            return None
        return self.exchange_outflow_usd / self.exchange_inflow_usd

    @property
    def whale_dominance(self) -> Optional[Decimal]:
        """Whale volume as % of total transaction volume"""
        if self.transaction_count and self.transaction_count > 0:
            return Decimal(self.whale_transaction_count) / self.transaction_count
        return None

    @property
    def observation_type(self) -> ObservationType:
        return ObservationType.ONCHAIN


class WhaleTransaction(BaseModel):
    """Individual whale transaction (value > threshold)"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset_pair: "AssetPair"
    timestamp: datetime
    tx_hash: str
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: Decimal
    amount_usd: Decimal
    is_exchange_deposit: bool = False
    is_exchange_withdrawal: bool = False
    source: str


class OnChainMetrics(BaseModel):
    """Aggregated on-chain metrics over a window"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset_pair: "AssetPair"
    window_start: datetime
    window_end: datetime
    total_inflow_usd: Decimal
    total_outflow_usd: Decimal
    net_flow_usd: Decimal
    whale_tx_count: int
    whale_volume_usd: Decimal
    avg_whale_tx_size_usd: Optional[Decimal] = None
    supply_on_exchanges_pct: Decimal
    supply_change_pct: Optional[Decimal] = None
    active_addresses_avg: Optional[Decimal] = None
    active_addresses_change_pct: Optional[Decimal] = None
    hash_rate_avg: Optional[Decimal] = None
    staking_ratio_avg: Optional[Decimal] = None
    source: str