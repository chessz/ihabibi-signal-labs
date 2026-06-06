"""
Feature engineering domain models for signals-lab
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict

from .enums import FeatureFamily

if TYPE_CHECKING:
    from .market import AssetPair


class FeatureDefinition(BaseModel):
    """Definition of a feature to be computed"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Unique feature name")
    family: FeatureFamily
    description: str = ""
    computation_function: str = Field(..., description="Function name in feature module")
    input_columns: List[str] = Field(..., description="Required input data columns")
    windows: List[str] = Field(default_factory=list, description="Lookback windows")
    params: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
    dependencies: List[str] = Field(
        default_factory=list,
        description="Names of features this depends on"
    )
    min_data_points: int = Field(default=50, ge=1)
    enabled: bool = True


class FeatureVector(BaseModel):
    """A single computed feature value"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset_pair: "AssetPair"
    timestamp: datetime
    feature_family: FeatureFamily
    feature_name: str = Field(..., description="Unique feature name")
    value: Decimal
    window: str = Field(default="1d", description="Computation window, e.g., 1h, 4h, 1d")
    computation_version: str = Field(default="1.0.0")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def key(self) -> str:
        """Unique key for deduplication"""
        return f"{self.asset_pair.normalized_symbol}:{self.feature_name}:{self.window}:{self.timestamp.isoformat()}"


class FeatureBatch(BaseModel):
    """Batch of feature vectors computed in one run"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    batch_id: str
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    features: List[FeatureVector]
    asset_pairs: List[str] = Field(default_factory=list)
    windows: List[str] = Field(default_factory=list)
    valid_from: datetime
    valid_to: datetime
    computation_time_ms: Optional[int] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class FeatureRegistryEntry(BaseModel):
    """Entry in the feature registry (persisted configuration)"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    family: FeatureFamily
    description: str
    computation_function: str
    input_columns: List[str]
    windows: List[str]
    params: Dict[str, Any]
    version: str
    dependencies: List[str]
    min_data_points: int
    enabled: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_computed_at: Optional[datetime] = None
    computation_count: int = 0
    avg_computation_ms: Optional[int] = None


from .market import AssetPair  # noqa: E402

FeatureVector.model_rebuild()