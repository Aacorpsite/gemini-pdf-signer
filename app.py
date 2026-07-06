import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from audio_recorder_streamlit import audio_recorder
from google import genai
from google.genai import types

# Make sure you add 'streamlit-google-auth' to your requirements.txt
from streamlit_google_auth import Authenticate

st.set_page_config(page_title="Gemini Smart PDF Pro", layout="wide")

# --- STEP 1: SECURE GOOGLE LOGIN ---
# In production, these client IDs come from your Google Developer Console
authenticator = Authenticate(
    secret_key="your_cookie_sign_key",
    client_id="your_google_client_id.apps.googleusercontent.com",
    client_secret="your_google_client_secret",
    redirect_uri="https://your-app-name.streamlit.app",
    cookie_name="google_user_session",
)

# Check if the user is logged in
user_info = authenticator.check_authenticator()

if not user_info:
    # If not logged in, show a clean, native Google button. No passwords, no IP text.
    st.title("📄 Welcome to PDF Smart Filler & Signer")
    st.write("Please sign in with your Google account to automatically link your saved profile information.")
    authenticator.login()

else:
    # --- STEP 2: APP LOADS ONCE LOGGED IN ---
    st.sidebar.image(user_info.get("picture", ""), width=50)
    st.sidebar.write(f"Hello, {user_info.get('name')}!")

    # Disconnect/Logout option
    if st.sidebar.button("Log out"):
        authenticator.logout()
        st.rerun()

    # Initialize Gemini using your live secure server key
    gemini_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else "YOUR_TEST_KEY"
    client = genai.Client(api_key=gemini_key)

    # --- AUTO-SAVE STORAGE ---
    if "pdf_data" not in st.session_state:
        st.session_state.pdf_data = None
    if "signature_saved" not in st.session_state:
        st.session_state.signature_saved = None

    st.title("🤖 Gemini AI Voice & Context PDF Smart-Filler")

    # --- GEMINI COGNITIVE FUNCTIONS ---
    def transcribe_audio_with_gemini(audio_bytes):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav'),
                          "Transcribe this audio clip completely and accurately."]
            )
            return response.text
        except Exception as e:
            return f"Audio Error: {str(e)}"

    def gemini_field_extractor(user_speech, field_name):
        try:
            prompt = f"Extract the data for a form field called '{field_name}' from this text: '{user_speech}'. If not mentioned, reply with 'NO_MATCH'. Otherwise, give only the value."
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            return response.text.strip()
        except:
            return "NO_MATCH"

    # --- MAIN ENGINE ---
    uploaded_file = st.file_uploader("Upload Document PDF", type=["pdf"])

    if uploaded_file is not None:
        if st.session_state.pdf_data is None:
            st.session_state.pdf_data = uploaded_file.read()

        doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
        page_num = st.number_input("Page Selector", min_value=1, max_value=len(doc), value=1) - 1
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)

        # Voice Input Capture Layer
        st.write("---")
        st.subheader("🎤 Speak to Gemini")
        audio_data = audio_recorder(text="Tap to Record Voice", recording_color="#4285F4", neutral_color="#1a73e8")

        voice_text = ""
        if audio_data:
            with st.spinner("Gemini processing audio..."):
                voice_text = transcribe_audio_with_gemini(audio_data)
                st.info(f"🗣️ Heard: *\"{voice_text}\"*")

        st.write("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            widgets = list(page.widgets())
            if widgets:
                st.subheader("⚡ Document Smart Fields")

                for widget in widgets:
                    f_name = widget.field_name.lower()
                    current_val = widget.field_value

                    # MAGICAL AUTOFILL: Pulls directly from Google Account payload seamlessly
                    if not current_val:
                        if "name" in f_name:
                            current_val = user_info.get("name", "")
                        elif "mail" in f_name:
                            current_val = user_info.get("email", "")

                    if voice_text:
                        gemini_match = gemini_field_extractor(voice_text, widget.field_name)
                        if gemini_match != "NO_MATCH":
                            current_val = gemini_match

                    new_val = st.text_input(f"Field: '{widget.field_name}'", value=current_val, key=f"gem_{widget.xref}")
                    if new_val != widget.field_value:
                        widget.field_value = new_val
                        widget.update()

                st.session_state.pdf_data = doc.write()

            # Drawing block for e-signatures
            st.subheader("🖊️ Draw E-Signature")
            canvas_result = st_canvas(fill_color="rgba(255, 255, 255, 0)", stroke_width=3, stroke_color="#0000FF", background_color="#eeeeee", height=120, width=300, drawing_mode="freedraw", key="gsig")
            sig_x = st.number_input("X Position", value=50)
            sig_y = st.number_input("Y Position", value=150)

            if st.button("💾 Apply Signature"):
                if canvas_result.image_data is not None:
                    st.session_state.signature_saved = {"page": page_num, "image": canvas_result.image_data, "x": sig_x, "y": sig_y}
                    st.rerun()

        with col2:
            st.subheader("👁️ Live Output View")
            output_doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")

            if st.session_state.signature_saved and st.session_state.signature_saved["page"] == page_num:
                sig = st.session_state.signature_saved
                p = output_doc[sig["page"]]
                scale_x, scale_y = p.rect.width / pix.width, p.rect.height / pix.height
                sig_img = Image.fromarray(sig["image"].astype('uint8'), 'RGBA')
                img_byte_arr = io.BytesIO()
                sig_img.save(img_byte_arr, format='PNG')
                rect = fitz.Rect(sig["x"] * scale_x, sig["y"] * scale_y, (sig["x"] + 120) * scale_x, (sig["y"] + 60) * scale_y)
                p.insert_image(rect, stream=img_byte_arr.getvalue())

            st.image(output_doc[page_num].get_pixmap(dpi=150).tobytes("png"), use_container_width=True)
            st.download_button(label="📥 Download Finished PDF", data=output_doc.write(), file_name="completed_form.pdf", mime="application/pdf")
          
