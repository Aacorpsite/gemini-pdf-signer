import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Smart Visual PDF Filler", layout="wide")
st.title("🎯 Direct Tap-to-Fill PDF Signer")
st.write("Tap directly inside any highlighted yellow form box on the document below to enter your information.")

# --- PERSISTENT STORAGE ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "field_values" not in st.session_state:
    st.session_state.field_values = {}  # Tracks field values by unique field names
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
    
    # Base layout background calculation rules
    base_image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")
    
    # Scale mappings to sync image pixels with PDF coordinates
    scale_x = base_image.width / page.rect.width
    scale_y = base_image.height / page.rect.height

    # --- AUTO-HIGHLIGHT INTERACTIVE LAYER ---
    highlight_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw_highlight = ImageDraw.Draw(highlight_layer)
    
    widgets = list(page.widgets())
    interactive_hitboxes = []

    # Map interactive form boundaries
    for widget in widgets:
        rect = widget.rect
        # Translate PDF vector spaces into visual pixel coordinate regions
        x0, y0, x1, y1 = rect.x0 * scale_x, rect.y0 * scale_y, rect.x1 * scale_x, rect.y1 * scale_y
        
        # Pull latest text inputs dynamically
        display_val = st.session_state.field_values.get(widget.field_name, widget.field_value or "")
        
        # Save structural metadata locations
        interactive_hitboxes.append({
            "name": widget.field_name, "widget": widget,
            "x0": x0, "y0": y0, "x1": x1, "y1": y1
        })
        
        # Draw soft semi-transparent neon highlights directly over blank spaces
        if widget.field_name == st.session_state.active_field:
            draw_highlight.rectangle([x0, y0, x1, y1], fill=(66, 133, 244, 80), outline=(66, 133, 244, 255), width=2) # Active blue
        else:
            draw_highlight.rectangle([x0, y0, x1, y1], fill=(255, 235, 59, 60), outline=(255, 193, 7, 180), width=1) # Fillable yellow

    # Flatten layers together cleanly
    preview_image = Image.alpha_composite(base_image, highlight_layer).convert("RGB")

    st.subheader("👁️ Click or Tap Highlighted Boxes Directly")
    
    # --- TAP TRACKING BOUNDARY DETECTOR ---
    click_coords = streamlit_image_coordinates(preview_image, key="pdf_interactive_grid")

    # Match tap locations with document field targets
    if click_coords is not None:
        tx, ty = click_coords["x"], click_coords["y"]
        
        # Scan if coordinates fall inside an active form box area
        matched_any = False
        for box in interactive_hitboxes:
            if box["x0"] <= tx <= box["x1"] and box["y0"] <= ty <= box["y1"]:
                st.session_state.active_field = box["name"]
                matched_any = True
                break
                
    # --- RENDERING FIELD TYPING INPUT CONTEXT ---
    if st.session_state.active_field:
        st.write("---")
        target_box = next((b for b in interactive_hitboxes if b["name"] == st.session_state.active_field), None)
        
        if target_box:
            st.markdown(f"🖋️ **Editing Field Row:** `{target_box['name']}`")
            current_typed_val = st.session_state.field_values.get(target_box["name"], target_box["widget"].field_value or "")
            
            # Simple text input field matching the target cell selection
            user_input_text = st.text_input("Enter text value details:", value=current_typed_val, key="active_input_box")
            
            col_save, col_clear = st.columns(2)
            with col_save:
                if st.button("Apply Field Text 💾"):
                    st.session_state.field_values[target_box["name"]] = user_input_text
                    # Burn modification back into document instance structure immediately
                    target_box["widget"].field_value = user_input_text
                    target_box["widget"].update()
                    st.session_state.pdf_data = doc.write()
                    st.session_state.active_field = None # Clear target selection on save
                    st.rerun()
            with col_clear:
                if st.button("Cancel / Close ❌"):
                    st.session_state.active_field = None
                    st.rerun()

    # --- PROCESS FINAL OUTBOUND GENERATION LAYER ---
    output_doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    
    st.write("---")
    st.subheader("📥 Export Final Copy")
    st.download_button(
        label="Download Completed Application PDF",
        data=output_doc.write(),
        file_name="completed_housing_form.pdf",
        mime="application/pdf"
    )
