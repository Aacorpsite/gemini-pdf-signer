import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Simple PDF Filler & Signer", layout="wide")
st.title("📝 Simple PDF Filler & Signer")
st.write("Upload any document, fill out the form boxes, draw your signature, and download the finished copy instantly.")

# --- AUTO-SAVE SESSION MEMORY ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "signature_saved" not in st.session_state:
    st.session_state.signature_saved = None

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload your PDF application form here:", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.pdf_data is None:
        st.session_state.pdf_data = uploaded_file.read()

    doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    
    if len(doc) > 1:
        page_num = st.number_input("Form Page Selector", min_value=1, max_value=len(doc), value=1) - 1
    else:
        page_num = 0
        
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    
    # --- FIXED MOBILE LAYOUT: PREVIEW FIRST ---
    st.subheader("👁️ Document Preview")
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
    
    st.download_button(
        label="📥 Download Finished PDF",
        data=output_doc.write(),
        file_name="completed_and_signed.pdf",
        mime="application/pdf"
    )
    st.write("---")

    # --- FIELDS & CONTROLS UNDERNEATH ---
    widgets = list(page.widgets())
    if widgets:
        st.subheader("🖋️ Fill Form Fields")
        for widget in widgets:
            new_val = st.text_input(f"Line: '{widget.field_name}'", value=widget.field_value, key=f"fld_{widget.xref}")
            if new_val != widget.field_value:
                widget.field_value = new_val
                widget.update()
        
        st.session_state.pdf_data = doc.write()
        st.write("---")

    st.subheader("🖊️ Draw Your Signature")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=3,
        stroke_color="#0000FF",
        background_color="#f0f2f6",
        height=120,
        width=300,
        drawing_mode="freedraw",
        key="signature_pad"
    )
    
    col_x, col_y = st.columns(2)
    with col_x:
        sig_x = st.number_input("Move Signature X (Left/Right)", value=50, step=10)
    with col_y:
        sig_y = st.number_input("Move Signature Y (Up/Down)", value=150, step=10)

    if st.button("💾 Apply Signature to Document"):
        if canvas_result.image_data is not None:
            st.session_state.signature_saved = {
                "page": page_num,
                "image": canvas_result.image_data,
                "x": sig_x,
                "y": sig_y
            }
            st.success("Signature locked in place!")
            st.rerun()
