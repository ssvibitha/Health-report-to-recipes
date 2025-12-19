import streamlit as st
import json
import re
from google import genai
from PIL import Image
import PyPDF2

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Personal Health & Kitchen",
    page_icon="🧬",
    layout="wide"
)

# --------------------------------------------------
# GEMINI INITIALIZATION
# --------------------------------------------------
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

MODEL_ID = "gemini-3-flash-preview"  # 👈 as you requested

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "clinical_data" not in st.session_state:
    st.session_state.clinical_data = None

# --------------------------------------------------
# APP TITLE
# --------------------------------------------------
st.title("🧬 Smart Health & Recipe Dashboard")

tab1, tab2 = st.tabs(["📄 Medical Analyzer", "🥗 Fridge Scanner"])

# ==================================================
# TAB 1: MEDICAL ANALYZER
# ==================================================
with tab1:
    st.header("1️⃣ Upload Clinical Report")

    uploaded_file = st.file_uploader(
        "Upload Medical TXT / PDF",
        type=["txt", "pdf"]
    )

    if uploaded_file:
        if uploaded_file.type == "text/plain":
            content = uploaded_file.read().decode("utf-8")
        else:
            reader = PyPDF2.PdfReader(uploaded_file)
            content = "\n".join(page.extract_text() or "" for page in reader.pages)

        if st.button("🔍 Extract Health Data"):
            with st.spinner("Analyzing clinical markers..."):
                prompt = """
Extract clinical data and return STRICT JSON ONLY.

Format:
{
  "conditions": [],
  "lab_markers": {},
  "medications": [],
  "summary": ""
}
"""

                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=[prompt, content]
                )

                try:
                    clean = re.sub(r"```json|```", "", response.text).strip()
                    st.session_state.clinical_data = json.loads(clean)
                    st.success("✅ Health data extracted")
                    st.json(st.session_state.clinical_data)
                except:
                    st.error("❌ Invalid JSON returned")
                    st.code(response.text)

# ==================================================
# TAB 2: FRIDGE SCANNER (FIXED & WORKING)
# ==================================================
with tab2:
    st.header("2️⃣ Kitchen Scan")

    if st.session_state.clinical_data:
        st.info("💡 Medical profile detected – recipes optimized.")
        with st.expander("📋 Active Health Profile"):
            st.json(st.session_state.clinical_data)
    else:
        st.warning("⚠️ No medical data – using general healthy rules.")

    img_buffer = st.camera_input("📸 Take a picture of your ingredients")

    if img_buffer and st.button("🍽️ Generate Recipes"):
        with st.spinner("Chef Gemini is analyzing your ingredients..."):

            # 👇 PIL Image (THIS IS THE KEY FIX)
            img = Image.open(img_buffer)

            health_context = json.dumps(
                st.session_state.clinical_data or {},
                indent=2
            )

            recipe_prompt = f"""
You are a professional medical nutritionist and chef.

1. Identify ingredients in the image.
2. Respect the medical profile below.
3. Suggest 10 HEALTHY dinner recipes.

Medical Profile:
{health_context}

For each recipe include:
- Recipe name
- Medical benefit
- Chef tip
"""

            # ✅ THIS WORKS WITH gemini-3-flash-preview
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[recipe_prompt, img]
            )

            st.markdown("---")
            st.markdown(response.text)
