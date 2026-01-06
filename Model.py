import streamlit as st
import json
import re
from google import genai
from PIL import Image
from pypdf import PdfReader
from datetime import datetime
import os
import pandas as pd
import streamlit.components.v1 as components

# PAGE CONFIG
st.set_page_config(
    page_title="HELIOS - Health Intelligence System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CUSTOM CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1rem 0;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1rem;
        font-style: italic;
        margin-bottom: 2rem;
    }
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #667eea;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# HELPER FUNCTIONS
def extract_numeric(text):
    match = re.search(r"[-+]?\d*\.\d+|\d+", str(text))
    return float(match.group()) if match else None

def load_users():
    if os.path.exists("users.json"):
        try:
            with open("users.json") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

def clean_json_response(text):
    clean = re.sub(r"```json\s*", "", text)
    clean = re.sub(r"```\s*", "", clean)
    clean = clean.strip()
    json_match = re.search(r'\{[\s\S]*\}', clean)
    if json_match:
        clean = json_match.group()
    return json.loads(clean)

# LOGIN LOGIC
users = load_users()

if 'username' not in st.session_state:
    st.markdown('<h1 class="main-header">HELIOS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Health-Enhanced Lifestyle Intelligence & Optimization System</p>', unsafe_allow_html=True)
    
    col_spacer1, col_login, col_spacer2 = st.columns([1, 2, 1])
    
    with col_login:
        st.markdown("---")
        st.markdown("## Welcome to HELIOS")
        st.markdown("Login or create an account to access your personalized health dashboard.")
        
        username = st.text_input("Username", key="login_user", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Login", type="primary", use_container_width=True):
                if not username or not password:
                    st.error("Please enter both username and password.")
                elif username in users and users[username] == password:
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
        
        with col_btn2:
            if st.button("Sign Up", use_container_width=True):
                if not username or not password:
                    st.warning("Please enter username and password.")
                elif username in users:
                    st.warning("Username already exists. Please choose another.")
                elif len(password) < 4:
                    st.warning("Password must be at least 4 characters.")
                else:
                    users[username] = password
                    save_users(users)
                    st.success("Account created successfully! Please login.")
        
        st.markdown("---")
        st.markdown("### System Features")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("**Medical Report Analysis**")
            st.markdown("**Smart Kitchen Scanner**")
        with col_f2:
            st.markdown("**Health Trend Tracking**")
            st.markdown("**Personalized Recommendations**")
    st.stop()

# GEMINI INITIALIZATION
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("GEMINI_API_KEY not found in secrets. Please add it to your Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-3-flash-preview"  # Changed to available model

# SESSION STATE
session_keys = {"clinical_data": None, "clinical_history": [], "recipe_history": []}
for key, default in session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default

# SIDEBAR
with st.sidebar:
    st.markdown(f"## Welcome, **{st.session_state.username}**")
    if st.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Health Profile Status")
    
    if st.session_state.clinical_data:
        st.success("Profile Active")
        data = st.session_state.clinical_data
        conditions = data.get("conditions", [])
        if conditions:
            st.markdown("**Active Conditions:**")
            for cond in conditions[:5]:
                st.markdown(f"• {cond}")
        markers = data.get("lab_markers", {})
        if markers:
            st.markdown("**Recent Markers:**")
            for marker, value in list(markers.items())[:3]:
                st.markdown(f"• {marker}: {value}")
        if st.button("Clear Profile", use_container_width=True):
            st.session_state.clinical_data = None
            st.rerun()
    else:
        st.warning("No Profile Loaded")
        st.caption("Upload a medical report to get personalized recommendations.")
    
    st.markdown("---")
    st.markdown("### Activity Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Reports", len(st.session_state.clinical_history))
    with col2:
        st.metric("Recipes", len(st.session_state.recipe_history))
    st.markdown("---")
    st.caption("HELIOS v2.0 - Health Intelligence System")

# MAIN HEADER
st.markdown('<h1 class="main-header">HELIOS</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Health-Enhanced Lifestyle Intelligence & Optimization System</p>', unsafe_allow_html=True)

# TABS - REMOVED PRODUCT SCANNER
tab1, tab2, tab3 = st.tabs(["Medical Analyzer", "Kitchen Scanner", "History & Trends"])

# TAB 1: MEDICAL ANALYZER
with tab1:
    st.markdown('<p class="section-header">Medical Report Analysis</p>', unsafe_allow_html=True)
    st.markdown("Upload your laboratory reports to extract health markers and build your personalized medical profile.")
    
    col_upload, col_info = st.columns([2, 1])
    
    with col_upload:
        uploaded_file = st.file_uploader("Upload Medical Report (PDF or TXT)", type=["txt", "pdf"], key="medical_uploader")
    
    with col_info:
        st.markdown("### Analysis Guidelines")
        st.markdown("- Upload laboratory test results\n- Blood work reports recommended\n- Ensure text is clearly readable\n- PDF or plain text formats accepted")
    
    if uploaded_file:
        try:
            if uploaded_file.type == "text/plain":
                content = uploaded_file.read().decode("utf-8")
            else:
                reader = PdfReader(uploaded_file)
                content = "\n".join(page.extract_text() or "" for page in reader.pages)
            
            if not content.strip():
                st.error("Could not extract text from the file.")
            else:
                with st.expander("Preview Extracted Text", expanded=False):
                    st.text_area("Content", content[:3000] + "..." if len(content) > 3000 else content, height=200, disabled=True)
                st.success(f"Successfully extracted {len(content)} characters from {uploaded_file.name}")
                
                if st.button("Analyze & Extract Health Markers", type="primary", use_container_width=True):
                    with st.spinner("Processing your medical report..."):
                        prompt = """You are a medical data extraction specialist. Analyze this medical report carefully and extract all relevant clinical information.

Return the data in this EXACT JSON format (no additional text):
{
    "conditions": ["list of diagnosed conditions"],
    "lab_markers": {"marker_name": "value with units"},
    "medications": ["list of medications"],
    "summary": "Brief 2-3 sentence summary"
}

Extract ALL lab values with units. If a field has no data, use empty list [] or object {}.
Analyze this report:"""
                        
                        try:
                            response = client.models.generate_content(model=MODEL_ID, contents=[prompt, content])
                            extracted_data = clean_json_response(response.text)
                            
                            st.session_state.clinical_data = extracted_data
                            st.session_state.clinical_history.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "filename": uploaded_file.name,
                                "data": extracted_data
                            })
                            
                            st.success("Medical Profile Updated Successfully!")
                            st.balloons()
                            
                            st.markdown("---")
                            st.markdown("### Extracted Information")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("#### Medical Conditions")
                                conditions = extracted_data.get("conditions", [])
                                if conditions:
                                    for cond in conditions:
                                        st.markdown(f"• {cond}")
                                else:
                                    st.info("No specific conditions identified")
                                
                                st.markdown("#### Current Medications")
                                medications = extracted_data.get("medications", [])
                                if medications:
                                    for med in medications:
                                        st.markdown(f"• {med}")
                                else:
                                    st.info("No medications mentioned")
                            
                            with col2:
                                st.markdown("#### Laboratory Markers")
                                markers = extracted_data.get("lab_markers", {})
                                if markers:
                                    for marker, value in markers.items():
                                        st.markdown(f"**{marker}:** {value}")
                                else:
                                    st.info("No lab markers found")
                            
                            st.markdown("#### Clinical Summary")
                            st.info(extracted_data.get("summary", "No summary available."))
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# TAB 2: KITCHEN SCANNER
with tab2:
    st.markdown('<p class="section-header">Smart Kitchen & Nutritional Analysis</p>', unsafe_allow_html=True)
    st.markdown("Scan your kitchen inventory to receive personalized, health-conscious recipe recommendations.")
    
    if st.session_state.clinical_data:
        st.success("Using your health profile for personalized recommendations")
    else:
        st.warning("No medical profile found. Upload a report for personalized suggestions.")
    
    st.markdown("---")
    col_input, col_pref = st.columns([1, 1])
    
    with col_input:
        st.markdown("### Image Capture")
        input_mode = st.radio("Select Image Source:", ["Upload Photos", "Use Camera"], horizontal=True, key="fridge_input_mode")
        fridge_images = []
        
        if input_mode == "Use Camera":
            cam_img = st.camera_input("Capture a photo of your kitchen inventory")
            if cam_img:
                fridge_images = [Image.open(cam_img)]
                st.success("Photo captured successfully")
        else:
            files = st.file_uploader("Upload photos of your kitchen", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="fridge_uploader")
            if files:
                fridge_images = [Image.open(f) for f in files]
                st.success(f"{len(files)} image(s) uploaded")
                if len(fridge_images) <= 4:
                    cols = st.columns(len(fridge_images))
                    for i, img in enumerate(fridge_images):
                        with cols[i]:
                            st.image(img, use_container_width=True)
    
    with col_pref:
        st.markdown("### Preferences")
        cuisine = st.multiselect("Cuisine Preferences", ["Indian", "Italian", "Mexican", "Mediterranean", "Asian", "American", "Middle Eastern", "French"], default=["Indian"], key="cuisine_select")
        meal = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"], key="meal_select")
        dietary = st.multiselect("Dietary Restrictions", ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Low-Carb", "Keto", "Nut-Free", "Low-Sodium"], key="dietary_select")
        cooking_time = st.select_slider("Available Cooking Time", options=["15 mins", "30 mins", "45 mins", "1 hour", "1+ hours"], value="30 mins")
    
    st.markdown("---")
    if fridge_images:
        if st.button("Analyze & Generate Personalized Recipes", type="primary", use_container_width=True):
            with st.spinner("Analyzing ingredients..."):
                prompt = f"""Analyze these kitchen images. User context: Health Profile: {json.dumps(st.session_state.clinical_data or {})}, Dietary: {", ".join(dietary) or "None"}, Cuisine: {", ".join(cuisine) or "Any"}, Meal: {meal}, Time: {cooking_time}

Provide:
1. DETECTED INGREDIENTS - List all visible items
2. NUTRITIONAL GAP ANALYSIS - What's missing for their health needs?
3. SHOPPING RECOMMENDATIONS - 5-7 items (ESSENTIAL/RECOMMENDED/OPTIONAL)
4. PERSONALIZED RECIPES (3) - Name, Time, Difficulty, Ingredients (available vs need), Instructions, Health Benefits"""
                
                try:
                    response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + fridge_images)
                    st.markdown("---")
                    st.markdown("## Personalized Kitchen Analysis")
                    st.markdown(response.text)
                    st.session_state.recipe_history.append({"timestamp": datetime.now().isoformat(), "meal": meal, "cuisines": cuisine, "content": response.text})
                    st.success("Analysis saved to history")
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
    else:
        st.info("Please upload photos to begin analysis.")

# TAB 3: HISTORY & TRENDS
with tab3:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown("##  Health Tracking & History")
    st.markdown("Track your lab values over time and review your past analyses.")
    
    # LAB MARKER TRENDS
    st.markdown("###  Lab Marker Trends")
    
    if st.session_state.clinical_history:
        # Prepare data for charting
        all_markers = []
        for entry in st.session_state.clinical_history:
            date = entry["timestamp"]
            markers = entry["data"].get("lab_markers", {})
            for m_name, m_val in markers.items():
                num_val = extract_numeric(m_val)
                if num_val is not None:
                    all_markers.append({
                        "Date": date, 
                        "Marker": m_name.lower().strip(), 
                        "Value": num_val
                    })
        
        if all_markers:
            df = pd.DataFrame(all_markers)
            unique_markers = sorted(df["Marker"].unique())
            
            col_select, col_info = st.columns([2, 1])
            
            with col_select:
                selected_marker = st.selectbox(
                    "Select a lab marker to visualize:", 
                    unique_markers,
                    key="trend_marker_select"
                )
            
            with col_info:
                marker_count = len(df[df["Marker"] == selected_marker])
                st.metric("Data Points", marker_count)
            
            plot_df = df[df["Marker"] == selected_marker].sort_values("Date")
            
            col_chart, col_stats = st.columns([2, 1])
            
            with col_chart:
                st.subheader(f" {selected_marker.title()} Over Time")
                st.line_chart(data=plot_df, x="Date", y="Value", height=350)
            
            with col_stats:
                st.subheader(" Statistics")
                
                if len(plot_df) >= 1:
                    current_val = plot_df["Value"].iloc[-1]
                    st.metric(label="Latest Value", value=f"{current_val:.2f}")
                    
                    if len(plot_df) > 1:
                        first_val = plot_df["Value"].iloc[0]
                        diff = current_val - first_val
                        percent = (diff / first_val) * 100 if first_val != 0 else 0
                        
                        st.metric(
                            label="First Value",
                            value=f"{first_val:.2f}"
                        )
                        
                        delta_color = "normal"
                        st.metric(
                            label="Total Change",
                            value=f"{abs(diff):.2f}",
                            delta=f"{percent:+.1f}%"
                        )
                        
                        st.metric(label="Readings", value=len(plot_df))
                        
                        # Trend indicator
                        if percent > 5:
                            st.warning(" Trending UP")
                        elif percent < -5:
                            st.info(" Trending DOWN")
                        else:
                            st.success(" Stable")
                    else:
                        st.info("Upload more reports to see trends")
        else:
            st.info("No numeric lab markers found in your reports. Upload a report with lab values to see trends.")
    else:
        st.info(" Upload medical reports in the 'Medical Analyzer' tab to track your health over time.")
    
    st.markdown("---")
    
    # HISTORY SECTIONS
    st.markdown("###  Complete History")
    
    col_h1, col_h2 = st.columns(2)
    
    with col_h1:
        st.markdown("####  Medical Reports")
        if st.session_state.clinical_history:
            for i, record in enumerate(reversed(st.session_state.clinical_history)):
                with st.expander(f" {record['timestamp']} - {record.get('filename', 'Report')}", expanded=False):
                    st.json(record['data'])
            
            if st.button(" Clear All Reports", key="clear_reports"):
                st.session_state.clinical_history = []
                st.session_state.clinical_data = None
                st.rerun()
        else:
            st.caption("No reports uploaded yet.")
    
    with col_h2:
        st.markdown("####  Recipe Suggestions")
        if st.session_state.recipe_history:
            for i, rec in enumerate(reversed(st.session_state.recipe_history)):
                meal_type = rec.get('meal', 'Meal')
                timestamp = rec['timestamp'][:10]
                with st.expander(f" {meal_type} - {timestamp}", expanded=False):
                    st.markdown(rec.get('content', ''))
            
            if st.button(" Clear Recipe History", key="clear_recipes"):
                st.session_state.recipe_history = []
                st.rerun()
        else:
            st.caption("No recipes generated yet.")
    
    # DATA EXPORT
    st.markdown("---")
    st.markdown("### Export Your Data")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        if st.session_state.clinical_history:
            export_data = json.dumps(st.session_state.clinical_history, indent=2, default=str)
            st.download_button(
                label="Download Medical Data",
                data=export_data,
                file_name=f"medical_history_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col_exp2:
        if st.session_state.recipe_history:
            export_data = json.dumps(st.session_state.recipe_history, indent=2, default=str)
            st.download_button(
                label="Download Recipes",
                data=export_data,
                file_name=f"recipe_history_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)

# FOOTER
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p><strong>HELIOS</strong> - Health-Enhanced Lifestyle Intelligence & Optimization System </p>
     <p style="font-size: 0.8rem;">Designed and developed by <strong>Sadhana, Teena, Vibitha & Vikasni</strong></p>
    <p style="font-size: 0.8rem;">Powered by AI - Built with Streamlit</p>
    <p style="font-size: 0.75rem; color: #999;">
        <em>This tool is for informational purposes only. Always consult a healthcare professional for medical advice.</em>
    </p>
</div>
""", unsafe_allow_html=True)

# Inject script into parent window to break out of iframe
components.html(
    """
    <script>
        const script = window.parent.document.createElement('script');
        script.src = "https://helioschat.linkpc.net:3443/js/chatbot-widget.js";
        script.async = true;
        script.onload = function() {
            console.log("Chatbot widget injected successfully");
        };
        window.parent.document.body.appendChild(script);
    </script>
    """,
    height=0,
    width=0
)