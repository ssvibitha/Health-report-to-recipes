import google.generativeai as genai
import os
from pydantic import BaseModel
from typing import List, Optional
import enum
import json

# --- 1. CONFIGURATION ---
API_KEY = "INSERT API KEY"   
genai.configure(api_key=API_KEY)

# --- 2. DATA MODELS (Schema using Pydantic) ---
class DocType(str, enum.Enum):
    LAB = "LAB_REPORT"
    RX = "PRESCRIPTION"
    NOTE = "CLINICAL_NOTE"
    OTHER = "OTHER"

class LabResult(BaseModel):
    test_name: str
    value: Optional[str]
    unit: Optional[str]
    is_abnormal: bool

class Medication(BaseModel):
    name: str
    dosage: str
    frequency: str

class MedicalReport(BaseModel):
    report_type: DocType
    patient_name: Optional[str]
    date: Optional[str]
    lab_results: Optional[List[LabResult]] = None
    medications: Optional[List[Medication]] = None
    clinical_summary: Optional[str] = None


# --- 3. PARSER FUNCTION (FIXED) ---
def parse_document(file_path: str) -> MedicalReport:
    ext = os.path.splitext(file_path)[1].lower()

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".pdf": "application/pdf",
        ".txt": "text/plain"
    }

    mime_type = mime_types.get(ext)
    if not mime_type:
        raise ValueError(f"Unsupported file type: {ext}")

    model = genai.GenerativeModel(
        model_name="gemini-3-flash-preview",
        generation_config={
            "response_mime_type": "application/json"
        }
    )

    print(f"--- Processing: {file_path} ---")

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        response = model.generate_content([
            """
            Extract medical information and return STRICT JSON only.
            JSON structure:
            {
              "report_type": "LAB_REPORT | PRESCRIPTION | CLINICAL_NOTE | OTHER",
              "patient_name": string or null,
              "date": string or null,
              "lab_results": [
                {"test_name": string, "value": string, "unit": string, "is_abnormal": boolean}
              ],
              "medications": [
                {"name": string, "dosage": string, "frequency": string}
              ],
              "clinical_summary": string or null
            }
            """,
            content
        ])

    else:
        with open(file_path, "rb") as f:
            doc_data = f.read()

        response = model.generate_content([
            """
            Extract medical information from this document and return STRICT JSON only
            using the defined schema.
            """,
            {"mime_type": mime_type, "data": doc_data}
        ])

    # --- 4. VALIDATE OUTPUT USING PYDANTIC ---
    raw_json = response.text

    try:
        validated_report = MedicalReport.model_validate_json(raw_json)
        return validated_report
    except Exception as e:
        print("❌ JSON validation failed")
        print(raw_json)
        raise e


# --- 5. RUN THE SCRIPT ---
if __name__ == "__main__":
    target_file = "target_file.txt"  # change to pdf / jpg / png

    if os.path.exists(target_file):
        report = parse_document(target_file)
        print("\n✅ Extracted Medical Report:")
        print(report.model_dump_json(indent=2))
    else:
        print(f"❌ File not found: {target_file}")
