import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Direct Tap PDF Filler", layout="wide")
st.title("🎯 Direct Tap-to-Fill PDF Signer")
st.write("Tap anywhere directly on the PDF form image below to type text or place your signature.")

# --- PERSISTENT STORAGE ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "placed_elements" not in st.session_state:
    st.session_state.placed_elements = []

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
    
    # Render the base image for display
    base_image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    
    # Preview layer: Draw temporary dots on the image so the user sees where they already typed
    preview_image = base_image.copy()
    draw = ImageDraw.Draw(preview_image)
    for el in st.session_state.placed_elements:
        if el["page"] == page_num:
            draw.ellipse([el["x"]-4, el["y"]-4, el["x"]+4, el["y"]+4], fill="#0000FF")

    st.subheader("👁️ Tap Document to Select Field Box")
    
    # --- ROCK-SOLID TAP CAPTURE ---
    # This component captures direct phone screen touches flawlessly without background errors
    value = streamlit_image_coordinates(preview_image, key="pdf_tap_grid")

    if value is not None:
        tap_x = value["x"]
        tap_y = value["y"]
        
        st.write("---")
        st.info(f"📍 Selected target coordinate line.")
        
        input_mode = st.radio("What would you like to place here?", ["Text / Information", "E-Signature"])
        
        if input_mode == "Text / Information":
            text_to_add = st.text_input("Type your text here:")
            font_size = st.slider("Font Size", min_value=10, max_value=24, value=14)
            
            if st.button("Apply Text to Form"):
                if text_to_add:
                    st.session_state.placed_elements.append({
                        "type": "text", "page": page_num, "content": text_to_add, 
                        "x": tap_x, "y": tap_y, "size": font_size
                    })
                    st.success("Text saved! Tap another spot to keep filling.")
                    st.rerun()
                    
        elif input_mode == "E-Signature":
            st.warning("Signature placement selected. Use the download area below to fetch your fully typed document first, or sign on your phone's native ink screen tool.")
            # Simple text placeholder fallback to avoid drawing pad dependencies
            if st.button("Place 'Signed' Text Stamp Here"):
                st.session_state.placed_elements.append({
                    "type": "text", "page": page_num, "content": "[Electronically Signed]", 
                    "x": tap_x, "y": tap_y, "size": 12
                })
                st.success("Signature stamp placed!")
                st.rerun()

    # --- RENDER ENGINE ---
    output_doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    
    for element in st.session_state.placed_elements:
        if element["page"] == page_num:
            p = output_doc[element["page"]]
            scale_x, scale_y = p.rect.width / base_image.width, p.rect.height / base_image.height
            
            if element["type"] == "text":
                p.insert_text(
                    fitz.Point(element["x"] * scale_x, (element["y"] + element["size"]/3) * scale_y), 
                    element["content"], fontsize=element["size"], color=(0, 0, 0)
                )

    st.write("---")
    st.subheader("📥 Process Completed File")
    st.download_button(
        label="Download Finished Application PDF",
        data=output_doc.write(),
        file_name="visually_filled_form.pdf",
        mime="application/pdf"
    )
