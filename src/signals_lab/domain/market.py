"""
Market domain models for signals-lab
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict

from .enums import DataSourceType, ObservationType


class AssetPair(BaseModel):
    """Trading pair with exchange information"""
    model_config = ConfigDict(frozen=True)
    
    symbol: str = Field(..., description="Trading symbol, e.g., BTC/USDT")
    base: str = Field(..., description="Base asset, e.g., BTC")
    quote: str = Field(..., description="Quote asset, e.g., USDT")
    exchange: str = Field(..., description="Exchange name, e.g., binance")
    is_active: bool = Field(default=True, description="Whether pair is actively traded")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def normalized_symbol(self) -> str:
        """Return normalized symbol for storage keys"""
        return f"{self.exchange}:{self.symbol}".replace("/", "_").upper()


class MarketObservation(BaseModel):
    """Raw market data observation (time-series)"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: AssetPair
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    spread_bps: Optional[int] = Field(default=None, description="Spread in basis points")
    realized_volatility: Optional[Decimal] = Field(default=None, description="Realized volatility")
    funding_rate: Optional[Decimal] = Field(default=None, description="Funding rate for perpetuals")
    open_interest: Optional[Decimal] = Field(default=None, description="Open interest for futures")
    source: str = Field(..., description="Data provider identifier")
    
    # Computed properties
    @property
    def mid_price(self) -> Decimal:
        return (self.high + self.low) / 2
    
    @property
    def typical_price(self) -> Decimal:
        return (self.high + self.low + self.close) / 3
    
    @property
    def vwap_approx(self) -> Decimal:
        """Approximate VWAP using typical price * volume"""
        return self.typical_price * self.volume
    
    @property
    def price_change_pct(self) -> Decimal:
        if self.open == 0:
            return Decimal("0")
        return ((self.close - self.open) / self.open) * 100
    
    @property
    def observation_type(self) -> ObservationType:
        return ObservationType.MARKET


class Candle(BaseModel):
    """OHLCV candle with metadata"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: AssetPair
    timestamp: datetime
    interval: str = Field(..., description="Candle interval, e.g., 1m, 1h, 1d")
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trades_count: Optional[int] = None
    taker_buy_volume: Optional[Decimal] = None
    taker_buy_trades: Optional[int] = None
    source: str = Field(..., description="Data provider identifier")
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def body_size(self) -> Decimal:
        return abs(self.close - self.open)
    
    @property
    def upper_wick(self) -> Decimal:
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> Decimal:
        return min(self.open, self.close) - self.low
    
    @property
    def range_size(self) -> Decimal:
        return self.high - self.low


class OrderBookSnapshot(BaseModel):
    """Order book snapshot for liquidity analysis"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: AssetPair
    timestamp: datetime
    bids: List[tuple[Decimal, Decimal]] = Field(
        default_factory=list,
        description="List of (price, quantity) tuples for bids"
    )
    asks: List[tuple[Decimal, Decimal]] = Field(
        default_factory=list,
        description="List of (price, quantity) tuples for asks"
    )
    source: str
    
    @property
    def best_bid(self) -> Optional[Decimal]:
        return self.bids[0][0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[Decimal]:
        return self.asks[0][0] if self.asks else None
    
    @property
    def spread(self) -> Optional[Decimal]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None
    
    @property
    def spread_bps(self) -> Optional[int]:
        if self.spread and self.best_bid:
            return int((self.spread / self.best_bid) * 10000)
        return None
    
    @property
    def bid_depth_usd(self) -> Decimal:
        return sum(price * qty for price, qty in self.bids)
    
    @property
    def ask_depth_usd(self) -> Decimal:
        return sum(price * qty for price, qty in self.asks)
    
    @property
    def order_book_imbalance(self) -> Optional[Decimal]:
        total_bid = self.bid_depth_usd
        total_ask = self.ask_depth_usd
        if total_bid + total_ask == 0:
            return None
        return (total_bid - total_ask) / (total_bid + total_ask)


class FundingRateObservation(BaseModel):
    """Funding rate observation for perpetual futures"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: AssetPair
    timestamp: datetime
    funding_rate: Decimal = Field(..., description="Funding rate (e.g., 0.0001 = 0.01%)")
    next_funding_time: Optional[datetime] = None
    mark_price: Optional[Decimal] = None
    index_price: Optional[Decimal] = None
    source: str
    
    @property
    def annualized_rate(self) -> Decimal:
        """Annualize funding rate (typically 3x per day)"""
        return self.funding_rate * 3 * 365


class OpenInterestObservation(BaseModel):
    """Open interest observation"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    asset_pair: AssetPair
    timestamp: datetime
    open_interest: Decimal = Field(..., description="Open interest in base asset")
    open_interest_usd: Optional[Decimal] = None
    source: str


class MarketDataBatch(BaseModel):
    """Batch of market observations for efficient ingestion"""
    observations: List[MarketObservation]
    candles: List[Candle] = Field(default_factory=list)
    order_books: List[OrderBookSnapshot] = Field(default_factory=list)
    funding_rates: List[FundingRateObservation] = Field(default_factory=list)
    open_interest: List[OpenInterestObservation] = Field(default_factory=list)
    received_at: datetime = Field(default_factory=datetime.utcnow)
    source: str