"""MVP 用の接種記録 JSON スキーマ。"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class VaccinationRecord(BaseModel):
    vaccine_name: Optional[str] = None
    dose_number: Optional[str] = None
    date: Optional[str] = Field(None, description="YYYY-MM-DD")
    manufacturer_lot: Optional[str] = Field(None, description="メーカー又は製剤名／ロット")
    clinic: Optional[str] = Field(None, description="医療機関名（接種者名欄のスタンプ）")
    remark: Optional[str] = Field(None, description="備考")
    confidence: Literal["high", "medium", "low"] = "medium"
    needs_review: bool = True


class VaccinationExtraction(BaseModel):
    child_name: Optional[str] = None
    vaccinations: list[VaccinationRecord] = Field(default_factory=list)


class ProcessImageResult(BaseModel):
    filename: str
    ocr_text: str


class ProcessResponse(BaseModel):
    child_name: Optional[str] = None
    vaccinations: list[VaccinationRecord]
    ocr_results: list[ProcessImageResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
