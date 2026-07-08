import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Smart Visual PDF Filler", layout="wide")
st.title("🎯 Direct Tap-to-Fill PDF Signer")

# --- PERSISTENT STORAGE ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "field_values" not in st.session_state:
    st.session_state.field_values = {}  
if "active_field" not in st.session_state:
    st.session_state.active_field = None

# --- FILE IMPORT ---
uploaded_file = st.file_uploader("Upload your document:", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.pdf_data is None:
        st.session_state.pdf_data = uploaded_file.read()

    doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    
    if len(doc) > 1:
        page_num = st.number_input("Page Selector", min_value=1, max_value=len(doc), value=1) - 1
    else:
        page_num = 0
        
    page = doc[page_num]
    pix = page.get_pixmap(dpi=120)
    
    base_image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")
    
    scale_x = base_image.width / page.rect.width
    scale_y = base_image.height / page.rect.height

    # --- AUTO-HIGHLIGHT INTERACTIVE LAYER ---
    highlight_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw_highlight = ImageDraw.Draw(highlight_layer)
    
    widgets = list(page.widgets())
    interactive_hitboxes = []

    for widget in widgets:
        rect = widget.rect
        x0, y0, x1, y1 = rect.x0 * scale_x, rect.y0 * scale_y, rect.x1 * scale_x, rect.y1 * scale_y
        
        interactive_hitboxes.append({
            "name": widget.field_name, "widget": widget,
            "x0": x0, "y0": y0, "x1": x1, "y1": y1
        })
        
        if widget.field_name == st.session_state.active_field:
            draw_highlight.rectangle([x0, y0, x1, y1], fill=(66, 133, 244, 100), outline=(66, 133, 244, 255), width=2)
        else:
            draw_highlight.rectangle([x0, y0, x1, y1], fill=(255, 235, 59, 70), outline=(255, 193, 7, 200), width=1)

    preview_image = Image.alpha_composite(base_image, highlight_layer).convert("RGB")

    # --- POP-UP MODAL ENGINE ---
    # This creates a professional pop-up box right on top of everything if a field is active
    @st.dialog("Fill Form Box")
    def fill_box_modal(target_box):
        st.markdown(f"📝 **Field:** `{target_box['name']}`")
        current_typed_val = st.session_state.field_values.get(target_box["name"], target_box["widget"].field_value or "")
        
        # This input fields gains immediate focus when the modal opens
        user_input_text = st.text_input("Start typing information:", value=current_typed_val, key="modal_input_box", autofocus=True)
        
        st.write("")
        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("Save 💾", use_container_width=True):
                st.session_state.field_values[target_box["name"]] = user_input_text
                target_box["widget"].field_value = user_input_text
                target_box["widget"].update()
                st.session_state.pdf_data = doc.write()
                st.session_state.active_field = None
                st.rerun()
        with col_clear:
            if st.button("Cancel ❌", use_container_width=True):
                st.session_state.active_field = None
                st.rerun()

    # --- TRACKING TOUCH COORDINATES ---
    click_coords = streamlit_image_coordinates(preview_image, key="pdf_interactive_grid")

    if click_coords is not None:
        tx, ty = click_coords["x"], click_coords["y"]
        
        for box in interactive_hitboxes:
            if box["x0"] <= tx <= box["x1"] and box["y0"] <= ty <= box["y1"]:
                if st.session_state.active_field != box["name"]:
                    st.session_state.active_field = box["name"]
                    # Open the pop-up immediately right where they look
                    fill_box_modal(box)
                    break
                
    # If a click happened outside but the session state is holding the active field, keep modal open
    elif st.session_state.active_field:
        active_box = next((b for b in interactive_hitboxes if b["name"] == st.session_state.active_field), None)
        if active_box:
            fill_box_modal(active_box)

    # --- PROCESS FINAL OUTPUT ---
    output_doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    st.write("---")
    st.download_button(
        label="📥 Download Completed PDF",
        data=output_doc.write(),
        file_name="completed_form.pdf",
        mime="application/pdf",
        use_container_width=True
    )
