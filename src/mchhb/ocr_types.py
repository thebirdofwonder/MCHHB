"""OCR レイアウト用データ型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def center_x(self) -> float:
        return (self.x_min + self.x_max) / 2

    @property
    def center_y(self) -> float:
        return (self.y_min + self.y_max) / 2

    @property
    def height(self) -> float:
        return max(self.y_max - self.y_min, 0.0)

    def vertical_overlap_ratio(self, other: "BBox") -> float:
        overlap = min(self.y_max, other.y_max) - max(self.y_min, other.y_min)
        if overlap <= 0:
            return 0.0
        smaller = min(self.height, other.height)
        return overlap / smaller if smaller > 0 else 0.0


@dataclass
class OcrLine:
    text: str
    bbox: BBox
    confidence: float = 1.0


@dataclass
class LayoutVaccinationRow:
    vaccine_name: Optional[str] = None
    date: Optional[str] = None
    manufacturer_lot: Optional[str] = None
    clinic: Optional[str] = None
    remark: Optional[str] = None
    bbox: Optional[BBox] = None
    confidence: float = 0.0


@dataclass
class DocumentOcrResult:
    text: str
    lines: list[OcrLine] = field(default_factory=list)
    layout_rows: list[LayoutVaccinationRow] = field(default_factory=list)
