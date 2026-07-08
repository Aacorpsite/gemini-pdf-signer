import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Direct Visual PDF Filler", layout="wide")
st.title("🎯 Direct Tap-to-Fill PDF Signer")
st.write("Tap anywhere directly on the PDF image below to type text or place your signature precisely where you want it.")

# --- PERSISTENT STORAGE LAYERS ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "placed_elements" not in st.session_state:
    st.session_state.placed_elements = []  # Keeps track of all added text/signatures

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
    pix = page.get_pixmap(dpi=120)  # Standardized crisp resolution
    
    # Clean conversion to strict PIL Image
    base_image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

    st.subheader("👁️ Tap Document to Select Field Box")
    
    # --- INTERACTIVE CLICK CANVAS ---
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 255, 0.1)",  
        stroke_width=2,
        stroke_color="#0000FF",
        background_image=base_image,
        update_streamlit=True,
        height=base_image.height,
        width=base_image.width,
        drawing_mode="point",  
        point_display_radius=4,
        key="pdf_interaction_canvas"
    )

    # --- POP-UP FIELD ENTRY CONTEXT ---
    if canvas_result.json_data and canvas_result.json_data["objects"]:
        last_object = canvas_result.json_data["objects"][-1]
        tap_x = last_object["left"]
        tap_y = last_object["top"]
        
        st.write("---")
        st.info(f"📍 Selected position on document alignment grid.")
        
        input_mode = st.radio("What would you like to place at this spot?", ["Text / Information", "E-Signature"])
        
        if input_mode == "Text / Information":
            text_to_add = st.text_input("Type your text here:")
            font_size = st.slider("Font Size", min_value=10, max_value=24, value=14)
            
            if st.button("Apply Text to This Box"):
                if text_to_add:
                    st.session_state.placed_elements.append({
                        "type": "text", "page": page_num, "content": text_to_add, 
                        "x": tap_x, "y": tap_y, "size": font_size
                    })
                    st.success("Inserted successfully!")
                    st.rerun()
                    
        elif input_mode == "E-Signature":
            st.write("Draw inside the box below:")
            sig_canvas = st_canvas(
                fill_color="rgba(0,0,0,0)", stroke_width=3, stroke_color="#0000FF",
                background_color="#f0f2f6", height=100, width=250, drawing_mode="freedraw", key="pop_sig"
            )
            if st.button("Stamp Signature onto Document Line"):
                if sig_canvas.image_data is not None:
                    st.session_state.placed_elements.append({
                        "type": "signature", "page": page_num, 
                        "content": sig_canvas.image_data, "x": tap_x, "y": tap_y
                    })
                    st.success("Signature stamped!")
                    st.rerun()

    # --- RENDER LAYER PROCESSOR ---
    output_doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    
    for element in st.session_state.placed_elements:
        if element["page"] == page_num:
            p = output_doc[element["page"]]
            scale_x, scale_y = p.rect.width / base_image.width, p.rect.height / base_image.height
            
            if element["type"] == "text":
                p.insert_text(
                    fitz.Point(element["x"] * scale_x, (element
            
