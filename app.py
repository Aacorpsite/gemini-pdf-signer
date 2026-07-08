import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image, ImageDraw

st.set_page_config(page_title="Reliable Mobile PDF Filler", layout="wide")
st.title("🎯 Mobile-Optimized PDF Filler")
st.write("Type your details into the corresponding numbered fields below, click 'Apply & Lock Changes', then download.")

# --- MEMORY CORES ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "field_values" not in st.session_state:
    st.session_state.field_values = {}

uploaded_file = st.file_uploader("Upload your document:", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.pdf_data is None:
        st.session_state.pdf_data = uploaded_file.read()

    doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    total_pages = len(doc)
    
    if total_pages > 1:
        page_num = st.number_input("Select Form Page", min_value=1, max_value=total_pages, value=1) - 1
    else:
        page_num = 0

    page = doc[page_num]
    widgets = list(page.widgets())

    # --- STEP 1: RENDER HIGHLIGHTED PDF PREVIEW AT THE TOP ---
    st.subheader("👁️ Document Page View")
    
    base_image = Image.open(io.BytesIO(page.get_pixmap(dpi=120).tobytes("png"))).convert("RGBA")
    scale_x = base_image.width / page.rect.width
    scale_y = base_image.height / page.rect.height

    highlight_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw_layer = ImageDraw.Draw(highlight_layer)

    # Label every yellow block with its corresponding number matching the input text line below
    for idx, widget in enumerate(widgets):
        rect = widget.rect
        x0, y0, x1, y1 = rect.x0 * scale_x, rect.y0 * scale_y, rect.x1 * scale_x, rect.y1 * scale_y
        
        # Soft yellow background highlight box
        draw_layer.rectangle([x0, y0, x1, y1], fill=(255, 235, 59, 90), outline=(255, 152, 0, 200), width=1)
        # Drop a small clear number indicator right on top of the yellow line box
        draw_layer.text((x0 + 2, y0 - 12), f"Field {idx + 1}", fill=(255, 0, 0, 255))

    preview_final = Image.alpha_composite(base_image, highlight_layer).convert("RGB")
    st.image(preview_final, use_container_width=True)
    st.write("---")

    # --- STEP 2: NATIVE FILLABLE TYPING LINES ---
    st.subheader("🖋️ Form Fields (Match Numbers with Image Above)")
    
    if widgets:
        for idx, widget in enumerate(widgets):
            field_label = widget.field_name if widget.field_name else f"Field {idx + 1}"
            current_saved_val = st.session_state.field_values.get(widget.field_name, widget.field_value or "")
            
            # Simple typing field that works flawlessly with phone keyboards
            st.text_input(
                f"👉 Line Number {idx + 1} ({field_label}):", 
                value=current_saved_val, 
                key=f"native_box_{widget.field_name}_{widget.xref}"
            )

        st.write("---")
        # Solid save execution controller button to bypass mobile tap-away errors entirely
        if st.button("💾 Apply & Lock Changes", use_container_width=True):
            for widget in widgets:
                user_typed_value = st.session_state[f"native_box_{widget.field_name}_{widget.xref}"]
                st.session_state.field_values[widget.field_name] = user_typed_value
                widget.field_value = user_typed_value
                widget.update()
            
            st.session_state.pdf_data = doc.write()
            st.success("All numbers permanently burned into the file! Ready to download.")
            st.rerun()
    else:
        st.info("No interactive form fields discovered on this page.")

    # --- STEP 3: MASTER FILE DOWNLOAD LINK ---
    st.write("---")
    st.download_button(
        label="📥 Download Completed PDF",
        data=st.session_state.pdf_data,
        file_name="completed_and_saved_form.pdf",
        mime="application/pdf",
        use_container_width=True
    )
