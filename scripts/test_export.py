"""Excel 出力の動作確認用スクリプト（API 不要）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mchhb.excel_export import export_to_excel
from mchhb.schema import ExtractionResult, VaccinationEntry

result = ExtractionResult(
    child_name="Sample Child",
    entries=[
        VaccinationEntry(
            vaccine_key="DPT",
            dose_number=1,
            dose_category="I期 初回",
            date="2001-02-05",
            manufacturer="DT「タケダ」",
            lot_number="HJ099B",
            institution="中央区 中央保健所",
            confidence="high",
        ),
        VaccinationEntry(
            vaccine_key="Polio",
            dose_number=1,
            date="2001-02-05",
            manufacturer="Oral Polio Vaccine",
            lot_number="66-1",
            institution="中央区 中央保健所",
            confidence="high",
        ),
        VaccinationEntry(
            vaccine_key="Japanese encephalitis",
            dose_number=4,
            dose_category="II期",
            date="2018-06-27",
            manufacturer="日本脳炎ワクチン",
            lot_number="JR155",
            institution="マイファミリークリニック蒲郡 守屋章成医師",
            confidence="high",
        ),
    ],
)

out = export_to_excel(result, Path("output/sample_vaccination_record.xlsx"))
print(f"Created: {out}")
