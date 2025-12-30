import streamlit as st
import asyncio
import logging
import os
import tempfile

from utils.service_utils import create_service_sections, validate_service_content
from utils.audio_utils import text_to_speech
from utils.video_utils import create_slide, combine_slides_and_audio
from services.unsplash_service import fetch_and_save_photo
from services.gemini_service import generate_slides_from_raw
from utils.avatar_utils import add_avatar_to_slide
from utils.pdf_extractor import extract_raw_content
from utils.pdf_utils import generate_service_pdf

logging.basicConfig(level=logging.INFO)

VOICES = {
    "en-IN-NeerjaNeural": "Neerja (Female, Indian English)",
    "en-IN-PrabhatNeural": "Prabhat (Male, Indian English)",
}


# -------------------------------------------------
# IMPROVED CSS STYLING
# -------------------------------------------------
def load_custom_css():
    """Load custom CSS for better UI in both light and dark modes"""
    css = """
    <style>
    /* ========================================
       BSK Training Video Generator - Modern UI
       Light & Dark Mode Support
       ======================================== */

    /* Light Mode Variables */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8f9fa;
        --bg-tertiary: #e9ecef;
        --text-primary: #212529;
        --text-secondary: #495057;
        --text-muted: #6c757d;
        --border-color: #dee2e6;
        --accent-primary: #0066cc;
        --accent-hover: #0052a3;
        --success-bg: #d1e7dd;
        --success-text: #0f5132;
        --error-bg: #f8d7da;
        --error-text: #842029;
        --warning-bg: #fff3cd;
        --warning-text: #664d03;
        --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
        --shadow-md: 0 4px 8px rgba(0,0,0,0.15);
        --shadow-lg: 0 8px 16px rgba(0,0,0,0.2);
    }

    /* Dark Mode Variables */
    [data-theme="dark"], 
    .stApp[data-theme="dark"],
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3a3a3a;
            --text-primary: #e4e4e4;
            --text-secondary: #b8b8b8;
            --text-muted: #8a8a8a;
            --border-color: #4a4a4a;
            --accent-primary: #4d9fff;
            --accent-hover: #6db0ff;
            --success-bg: #1a4d2e;
            --success-text: #90ee90;
            --error-bg: #4d1f1f;
            --error-text: #ff9999;
            --warning-bg: #4d4520;
            --warning-text: #ffd966;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 8px rgba(0,0,0,0.4);
            --shadow-lg: 0 8px 16px rgba(0,0,0,0.5);
        }
    }

    /* Global Styles */
    .stApp {
        background-color: var(--bg-primary);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%) !important;
        border-right: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] .element-container {
        color: var(--text-primary);
    }

    [data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 1.3rem;
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-secondary) !important;
        line-height: 1.6;
    }

    [data-testid="stSidebar"] .stMarkdown strong {
        color: var(--text-primary) !important;
    }

    [data-testid="stSidebar"] .stMarkdown em {
        color: var(--accent-primary) !important;
        font-style: normal;
        font-weight: 500;
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--border-color);
        margin: 1.5rem 0;
        opacity: 0.5;
    }

    /* Main Content Area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 700;
    }

    .main h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .main h2 {
        font-size: 1.5rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: var(--text-primary) !important;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-color);
    }

    /* Text and Paragraphs */
    p, div, span {
        color: var(--text-primary) !important;
    }

    .stMarkdown {
        color: var(--text-secondary) !important;
    }

    /* Input Fields */
    .stTextInput input,
    .stTextArea textarea {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease;
        font-size: 0.95rem !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(77, 159, 255, 0.15) !important;
        outline: none !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
        opacity: 0.7;
    }

    /* Labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stFileUploader label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem;
        font-size: 0.95rem !important;
    }

    .stTextInput label p,
    .stTextArea label p,
    .stSelectbox label p,
    .stFileUploader label p {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* Form Container */
    .stForm {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border: 2px solid var(--border-color);
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: var(--shadow-md);
        margin: 1.5rem 0;
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover)) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-sm) !important;
        text-transform: none !important;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md) !important;
        background: linear-gradient(135deg, var(--accent-hover), var(--accent-primary)) !important;
    }

    .stButton button:active {
        transform: translateY(0);
    }

    .stFormSubmitButton button {
        background: linear-gradient(135deg, #28a745, #20853a) !important;
        width: 100%;
        padding: 1rem !important;
        font-size: 1.1rem !important;
    }

    .stFormSubmitButton button:hover {
        background: linear-gradient(135deg, #20853a, #28a745) !important;
    }

    /* Download Button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #6f42c1, #5a32a3) !important;
        color: white !important;
    }

    .stDownloadButton button:hover {
        background: linear-gradient(135deg, #5a32a3, #6f42c1) !important;
    }

    /* File Uploader */
    .stFileUploader {
        background-color: var(--bg-secondary);
        border: 2px dashed var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        transition: all 0.3s ease;
    }

    .stFileUploader:hover {
        border-color: var(--accent-primary);
        background-color: var(--bg-tertiary);
    }

    .stFileUploader label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    .stFileUploader section {
        background-color: transparent !important;
    }

    .stFileUploader button {
        background-color: var(--accent-primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background-color: var(--bg-secondary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox [data-baseweb="select"] {
        background-color: var(--bg-secondary) !important;
    }

    .stSelectbox [data-baseweb="select"] > div {
        background-color: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox [data-baseweb="select"] span {
        color: var(--text-primary) !important;
    }

    /* Dropdown Menu */
    [data-baseweb="popover"] {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--shadow-lg) !important;
    }

    [role="listbox"] {
        background-color: var(--bg-secondary) !important;
    }

    [role="option"] {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
    }

    [role="option"]:hover {
        background-color: var(--bg-tertiary) !important;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-hover)) !important;
    }

    .stProgress > div {
        background-color: var(--bg-tertiary) !important;
        border-radius: 10px;
        overflow: hidden;
        height: 12px !important;
    }

    /* Alert Messages */
    [data-baseweb="notification"] {
        background-color: var(--bg-secondary) !important;
        border-radius: 10px !important;
        box-shadow: var(--shadow-md) !important;
        border-left: 4px solid !important;
        padding: 1rem 1.5rem !important;
    }

    /* Success Alert */
    [data-baseweb="notification"][kind="positive"],
    .stSuccess {
        background-color: var(--success-bg) !important;
        border-left-color: #28a745 !important;
    }

    [data-baseweb="notification"][kind="positive"] div,
    .stSuccess div {
        color: var(--success-text) !important;
    }

    /* Error Alert */
    [data-baseweb="notification"][kind="negative"],
    .stError {
        background-color: var(--error-bg) !important;
        border-left-color: #dc3545 !important;
    }

    [data-baseweb="notification"][kind="negative"] div,
    .stError div {
        color: var(--error-text) !important;
    }

    /* Warning Alert */
    [data-baseweb="notification"][kind="warning"],
    .stWarning {
        background-color: var(--warning-bg) !important;
        border-left-color: #ffc107 !important;
    }

    [data-baseweb="notification"][kind="warning"] div,
    .stWarning div {
        color: var(--warning-text) !important;
    }

    /* Info Alert */
    [data-baseweb="notification"][kind="info"],
    .stInfo {
        background-color: var(--bg-tertiary) !important;
        border-left-color: var(--accent-primary) !important;
    }

    [data-baseweb="notification"][kind="info"] div,
    .stInfo div {
        color: var(--text-primary) !important;
    }

    /* Video Player */
    .stVideo {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: var(--shadow-lg);
        margin: 1.5rem 0;
        border: 2px solid var(--border-color);
    }

    /* Columns */
    .row-widget {
        gap: 1.5rem;
    }

    [data-testid="column"] {
        background-color: transparent;
        padding: 0.5rem;
    }

    /* Divider */
    hr {
        border-color: var(--border-color) !important;
        margin: 2rem 0 !important;
        opacity: 0.5;
    }

    /* Caption Text */
    .stCaption {
        color: var(--text-muted) !important;
        font-size: 0.875rem !important;
    }

    .stCaption p {
        color: var(--text-muted) !important;
    }

    /* Balloons Animation */
    .balloons {
        z-index: 9999;
    }

    /* Empty State */
    .stInfo p {
        color: var(--text-primary) !important;
        font-size: 1rem;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 5px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }

    /* Custom Classes */
    .section-header {
        background: linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary));
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border-left: 4px solid var(--accent-primary);
        margin: 1.5rem 0 1rem 0;
    }

    .section-header h2 {
        margin: 0 !important;
        border: none !important;
        padding: 0 !important;
    }

    .status-box {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        font-weight: 500;
        color: var(--text-primary) !important;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .main h1 {
            font-size: 2rem;
        }
        
        .main h2 {
            font-size: 1.3rem;
        }
        
        .stForm {
            padding: 1.5rem;
        }

        .row-widget {
            flex-direction: column;
        }
    }

    /* Animation */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .main .block-container {
        animation: fadeIn 0.4s ease-out;
    }

    /* Required Field Asterisk */
    .stTextInput label::after,
    .stTextArea label::after {
        content: '';
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    st.set_page_config(
        page_title="BSK Training Video Generator",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load improved CSS
    load_custom_css()

    # Also try to load external CSS if exists
    css_path = os.path.join("assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        st.markdown("### 🎥 BSK Training Generator")
        st.markdown("**Professional Training Videos**")
        st.markdown("*Bangla Sahayta Kendra*")
        st.markdown("---")

        page = st.selectbox(
            "📑 Select Page:",
            ["🎬 Create New Video", "📂 View Existing Videos"],
            key="page_selector",
        )

        st.markdown("---")
        st.markdown("### 🎙️ Voice Settings")

        voice_keys = list(VOICES.keys())
        voice_labels = list(VOICES.values())
        voice_index = st.selectbox(
            "Choose Narrator Voice:",
            range(len(voice_keys)),
            format_func=lambda i: voice_labels[i],
        )
        selected_voice = voice_keys[voice_index]

        st.markdown("---")
        st.markdown("### 📄 Upload Options")
        st.caption("Upload a PDF to auto-generate content")
        uploaded_pdf = st.file_uploader(
            "Upload Service PDF",
            type=["pdf"],
            help="If provided, form content will be ignored and PDF content will be used instead",
        )

        st.markdown("---")
        st.markdown("### 🧑‍🏫 AI Avatar")
        st.caption("Avatar will appear in the generated video")

    # ---------------- ROUTING ----------------
    if page == "🎬 Create New Video":
        show_create_video_page(selected_voice, uploaded_pdf)
    else:
        show_existing_videos_page()


# -------------------------------------------------
# CREATE VIDEO PAGE
# -------------------------------------------------
def show_create_video_page(selected_voice, uploaded_pdf):
    st.title("🎥 BSK Training Video Generator")
    st.markdown("**Create professional training videos for BSK data entry operators**")
    st.markdown("---")

    # ---------------- FORM UI ----------------
    with st.form("service_form"):
        st.markdown('<div class="section-header"><h2>📋 Service Training Information</h2></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            service_name = st.text_input(
                "Service Name *",
                placeholder="e.g., Aadhaar Card Application",
                help="Enter the name of the government service"
            )
            service_description = st.text_area(
                "Service Description *",
                height=100,
                placeholder="Provide a brief overview of the service...",
                help="Describe what this service does"
            )

        with col2:
            how_to_apply = st.text_area(
                "Step-by-Step Application Process *",
                height=100,
                placeholder="1. Visit the portal\n2. Fill the form\n3. Upload documents...",
                help="Detailed steps for applying"
            )
            eligibility_criteria = st.text_area(
                "Eligibility Criteria *",
                height=100,
                placeholder="Who can apply for this service...",
                help="Requirements to be eligible"
            )

        required_docs = st.text_area(
            "Required Documents *",
            height=80,
            placeholder="• Aadhaar Card\n• Address Proof\n• Photo...",
            help="List all necessary documents"
        )

        st.markdown('<div class="section-header"><h2>🎯 Training Specific Information</h2></div>', unsafe_allow_html=True)
        
        col3, col4 = st.columns(2)

        with col3:
            operator_tips = st.text_area(
                "Operator Tips (Optional)",
                height=100,
                placeholder="Important tips for data entry operators...",
                help="Special instructions for operators"
            )
            service_link = st.text_input(
                "Official Service Link (Optional)",
                placeholder="https://example.gov.in/service",
                help="Direct link to the service portal"
            )

        with col4:
            troubleshooting = st.text_area(
                "Common Issues & Solutions (Optional)",
                height=100,
                placeholder="Issue: Form not loading\nSolution: Clear browser cache...",
                help="Common problems and their fixes"
            )
            fees_and_timeline = st.text_input(
                "Fees & Processing Time (Optional)",
                placeholder="Fee: ₹50 | Processing: 7-10 days",
                help="Cost and expected timeline"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Generate Training Video", use_container_width=True)

    # ---------------- GENERATION LOGIC ----------------
    if submitted:
        try:
            progress = st.progress(0, text="Initializing video generation...")
            status = st.empty()

            video_clips = []
            audio_paths = []

            # ==================================================
            # CASE 1: PDF EXISTS → IGNORE FORM
            # ==================================================
            if uploaded_pdf:
                with status.container():
                    st.markdown('<div class="status-box">📄 Extracting content from PDF (form data ignored)...</div>', unsafe_allow_html=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_pdf.read())
                    pdf_path = tmp.name

                pages = extract_raw_content(pdf_path)
                raw_text = "\n".join(line for page in pages for line in page["lines"])
                
                # Use PDF filename as service name
                service_name = uploaded_pdf.name.replace(".pdf", "")

            # ==================================================
            # CASE 2: FORM → RAW TEXT
            # ==================================================
            else:
                service_content = {
                    "service_name": service_name,
                    "service_description": service_description,
                    "how_to_apply": how_to_apply,
                    "eligibility_criteria": eligibility_criteria,
                    "required_docs": required_docs,
                    "operator_tips": operator_tips,
                    "troubleshooting": troubleshooting,
                    "service_link": service_link,
                    "fees_and_timeline": fees_and_timeline,
                }

                valid, msg = validate_service_content(service_content)
                if not valid:
                    st.error(f"❌ Validation Error: {msg}")
                    return

                # 1️⃣ Generate & SAVE PDF
                with status.container():
                    st.markdown('<div class="status-box">📄 Generating training PDF from form data...</div>', unsafe_allow_html=True)
                
                progress.progress(10, text="Generating PDF document...")
                pdf_path = generate_service_pdf(service_content)

                # Optional: show download button
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "📥 Download Training PDF",
                        data=f.read(),
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf",
                        use_container_width=True
                    )

                # 2️⃣ Extract text from the saved PDF
                pages = extract_raw_content(pdf_path)
                raw_text = "\n".join(line for page in pages for line in page["lines"])

            # ==================================================
            # GEMINI → SLIDES (NEW API)
            # ==================================================
            with status.container():
                st.markdown('<div class="status-box">🧠 Structuring training slides using AI...</div>', unsafe_allow_html=True)
            
            progress.progress(20, text="Processing content with AI...")
            slides_response = generate_slides_from_raw(raw_text)
            slides = slides_response["slides"]

            st.info(f"✅ Generated {len(slides)} training slides")

            # ==================================================
            # VIDEO PIPELINE
            # ==================================================
            for i, slide in enumerate(slides):
                with status.container():
                    st.markdown(f'<div class="status-box">🎬 Creating slide {i + 1} of {len(slides)}: {slide["title"]}</div>', unsafe_allow_html=True)

                progress.progress(int(20 + (i / len(slides) * 60)), text=f"Processing slide {i + 1}/{len(slides)}...")

                narration = " ".join(slide["bullets"])
                audio = asyncio.run(text_to_speech(narration, voice=selected_voice))
                audio_paths.append(audio)

                try:
                    image = fetch_and_save_photo(slide["image_keyword"])
                except Exception as img_error:
                    logging.warning(f"Image fetch failed: {img_error}. Using fallback.")
                    # Fallback to default image if fetch fails
                    fallback = os.path.join("images", "fallback_video.jpg")
                    if not os.path.exists(fallback):
                        # Create a simple fallback if it doesn't exist
                        try:
                            from PIL import Image
                            os.makedirs("images", exist_ok=True)
                            img = Image.new("RGB", (1280, 720), (30, 30, 40))
                            img.save(fallback, "JPEG", quality=90)
                        except Exception:
                            pass
                    image = fallback if os.path.exists(fallback) else os.path.join("assets", "default_background.jpg")

                clip = create_slide(slide["title"], slide["bullets"], image, audio)
                clip = add_avatar_to_slide(clip, audio_duration=clip.duration)
                video_clips.append(clip)

            with status.container():
                st.markdown('<div class="status-box">🎞️ Rendering final video...</div>', unsafe_allow_html=True)
            
            progress.progress(90, text="Finalizing video...")
            final_path = combine_slides_and_audio(
                video_clips, audio_paths, service_name=service_name or "BSK_Service"
            )

            progress.progress(100, text="✅ Complete!")
            st.session_state["video_path"] = final_path
            st.session_state["audio_paths"] = audio_paths

            status.empty()
            progress.empty()

            st.success("✅ Training video generated successfully!")
            st.balloons()

        except Exception as e:
            logging.error(f"Video generation error: {e}")
            st.error(f"❌ Error generating video: {str(e)}")
            st.error("Please check your inputs and try again.")

    # ---------------- DISPLAY RESULT ----------------
    if "video_path" in st.session_state:
        st.markdown("---")
        st.markdown("## 🎬 Generated Training Video")

        with open(st.session_state["video_path"], "rb") as f:
            st.video(f.read())

        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.download_button(
                "📥 Download Video",
                data=open(st.session_state["video_path"], "rb").read(),
                file_name=os.path.basename(st.session_state["video_path"]),
                mime="video/mp4",
                use_container_width=True
            )
        
        with col2:
            if st.button("🔄 Generate New", use_container_width=True):
                st.session_state.clear()
                st.rerun()


# -------------------------------------------------
# EXISTING VIDEOS PAGE
# -------------------------------------------------
def show_existing_videos_page():
    st.title("📂 Existing Training Videos")
    st.markdown("**Browse and view previously generated training videos**")
    st.markdown("---")

    output_dir = "output_videos"
    if not os.path.exists(output_dir):
        st.info("📭 No videos found. Create your first video to get started!")
        return

    videos = sorted([f for f in os.listdir(output_dir) if f.endswith(".mp4")], reverse=True)
    
    if not videos:
        st.info("📭 No videos available yet. Generate some videos first!")
        return

    st.success(f"✅ Found {len(videos)} training video(s)")
    
    selected = st.selectbox(
        "Select a video to view:",
        videos,
        format_func=lambda x: x.replace("_", " ").replace(".mp4", "")
    )
    
    if selected:
        path = os.path.join(output_dir, selected)
        
        st.markdown("### 🎥 Video Preview")
        with open(path, "rb") as f:
            video_bytes = f.read()
            st.video(video_bytes)
        
        # File info
        file_size = os.path.getsize(path) / (1024 * 1024)  # Convert to MB
        st.caption(f"📊 File size: {file_size:.2f} MB")
        
        st.download_button(
            "📥 Download This Video",
            data=open(path, "rb").read(),
            file_name=selected,
            mime="video/mp4",
            use_container_width=True
        )


# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    main()
