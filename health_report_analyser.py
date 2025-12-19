from google import genai
from google.genai.errors import ClientError
import os
import json
import time
from typing import List, Optional
from pydantic import BaseModel
import enum

# ================= CONFIG =================
API_KEY = "INSERT API key"   # 🔴 must have quota/billing
MODEL_NAME = "gemini-3-flash-preview"  # safer than 2.0
OUTPUT_FILE = "medical_report.json"

client = genai.Client(api_key=API_KEY)

# ================= DATA MODELS =================
class DocType(str, enum.Enum):
    LAB = "LAB_REPORT"
    RX = "PRESCRIPTION"
    NOTE = "CLINICAL_NOTE"
    OTHER = "OTHER"

class LabResult(BaseModel):
    test_name: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None
    is_abnormal: Optional[bool] = None

class Medication(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None

class MedicalReport(BaseModel):
    report_type: Optional[DocType] = None
    patient_name: Optional[str] = None
    date: Optional[str] = None
    lab_results: Optional[List[LabResult]] = None
    medications: Optional[List[Medication]] = None
    clinical_summary: Optional[str] = None

# ================= GEMINI CALL (SAFE) =================
def call_gemini(prompt: str, content: str):
    try:
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, content],
            config={"temperature": 0.1}
        )
    except ClientError as e:
        if "RESOURCE_EXHAUSTED" in str(e):
            print("\n❌ GEMINI QUOTA EXCEEDED")
            print("👉 Enable billing or wait for quota reset")
            print("👉 https://ai.google.dev/usage")
            return None
        else:
            raise e

# ================= PARSER =================
def parse_document(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    prompt = """
    Extract medical information and return STRICT JSON ONLY.
    Use null for missing values.

    Schema:
    {
      "report_type": "LAB_REPORT | PRESCRIPTION | CLINICAL_NOTE | OTHER",
      "patient_name": string | null,
      "date": string | null,
      "lab_results": [
        {"test_name": string, "value": string, "unit": string, "is_abnormal": boolean}
      ],
      "medications": [
        {"name": string, "dosage": string, "frequency": string}
      ],
      "clinical_summary": string | null
    }
    """

    response = call_gemini(prompt, content)
    if response is None:
        return {"error": "Quota exceeded. No API call made."}

    raw = response.text.strip()

    # Try validation
    try:
        report = MedicalReport.model_validate_json(raw)
        return report.model_dump()
    except Exception:
        # Fallback: save raw JSON
        try:
            return json.loads(raw)
        except Exception:
            return {"error": "Invalid JSON returned by model"}

# ================= SAVE JSON =================
def save_json(data: dict):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\n✅ JSON saved to {OUTPUT_FILE}")

# ================= MAIN =================
if __name__ == "__main__":
    target_file = "target_file.txt"

    if not os.path.exists(target_file):
        print("❌ Input file not found")
        exit()

    data = parse_document(target_file)
    save_json(data)
