"""In-memory models shared by collection and release calculation."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd

SourceState = Literal["APPROVED", "FAILED"]


@dataclass(frozen=True)
class SourceStatus:
    source_id: str
    status: SourceState
    as_of: str | None
    message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "sourceId": self.source_id,
            "status": self.status,
            "asOf": self.as_of,
            "message": self.message,
        }


@dataclass(frozen=True)
class UniverseSnapshot:
    members: tuple[str, ...]
    observed_at: date
    source_id: str


@dataclass(frozen=True)
class BreadthInput:
    universe: UniverseSnapshot
    prices: pd.DataFrame


@dataclass(frozen=True)
class VixSnapshot:
    as_of: date
    value: float
    previous_as_of: date | None = None
    previous_value: float | None = None
    history: pd.Series | None = None


@dataclass(frozen=True)
class TreasurySnapshot:
    as_of: date
    treasury_2y: float
    treasury_10y: float
    treasury_2y_change_1d_bp: float
    treasury_10y_change_1d_bp: float
    treasury_10y_change_3d_bp: float


@dataclass(frozen=True)
class OfrSnapshot:
    as_of: date
    value: float
    components: dict[str, float]
    regions: dict[str, float]
    history: pd.DataFrame | None = None


@dataclass(frozen=True)
class CftcSnapshot:
    as_of: date
    history: pd.DataFrame


@dataclass(frozen=True)
class CollectedMarketData:
    market_as_of: date
    core_prices: pd.DataFrame
    breadth: dict[str, BreadthInput]
    fred_series: dict[str, pd.Series] | None
    vix: VixSnapshot | None
    ofr: OfrSnapshot | None
    source_status: tuple[SourceStatus, ...]
    treasury: TreasurySnapshot | None = None
    cftc: CftcSnapshot | None = None
