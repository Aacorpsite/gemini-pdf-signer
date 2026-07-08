import streamlit as st
import fitz  # PyMuPDF
import io
import base64
from PIL import Image

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🎯 Direct Visual PDF Signer")

if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "field_values" not in st.session_state:
    st.session_state.field_values = {}

uploaded_file = st.file_uploader("Upload your document:", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.pdf_data is None:
        st.session_state.pdf_data = uploaded_file.read()

    # Read layout query strings passed back from the JavaScript layer
    query_params = st.query_params
    if "update_field" in query_params:
        f_name = query_params["update_field"]
        f_val = query_params.get("value", "")
        
        # Save value and burn immediately back into the active PDF structure
        st.session_state.field_values[f_name] = f_val
        doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
        for widget in doc[0].widgets():  # Direct page 1 tracking
            if widget.field_name == f_name:
                widget.field_value = f_val
                widget.update()
                break
        st.session_state.pdf_data = doc.write()
        # Clear out query parameters and refresh cleanly
        st.query_params.clear()
        st.rerun()

    doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(dpi=130)
    
    # Process base image array string stream
    img_bytes = pix.tobytes("png")
    encoded_img = base64.b64encode(img_bytes).decode("utf-8")
    
    # Target scale dimensions
    img_w = pix.width
    img_h = pix.height
    scale_x = img_w / page.rect.width
    scale_y = img_h / page.rect.height

    # Build individual inline inputs using direct HTML coordinate style properties
    input_elements_html = ""
    for widget in page.widgets():
        r = widget.rect
        x = r.x0 * scale_x
        y = r.y0 * scale_y
        w = (r.x1 - r.x0) * scale_x
        h = (r.y1 - r.x0) * scale_y if (r.y1 - r.y0) < 15 else (r.y1 - r.y0) * scale_y
        
        current_val = st.session_state.field_values.get(widget.field_name, widget.field_value or "")
        
        # Injects direct transparent box inputs sitting perfectly on top of the yellow highlighted document lines
        input_elements_html += f"""
        <input type="text" value="{current_val}" 
            style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px; 
                   background-color: rgba(255, 235, 59, 0.35); border: 1px solid #ffc107; 
                   font-size: 13px; font-family: sans-serif; padding: 0px 2px; box-sizing: border-box;"
            onblur="parent.window.location.search = '?update_field=' + encodeURIComponent('{widget.field_name}') + '&value=' + encodeURIComponent(this.value);"
        />
        """

    # Combine background PDF image layer and interactive inputs together flawlessly
    workspace_html = f"""
    <div style="position: relative; width: {img_w}px; height: {img_h}px; margin: 0 auto; user-select: none;">
        <img src="data:image/png;base64,{encoded_img}" style="width: 100%; height: 100%; display: block;" />
        {input_elements_html}
    </div>
    """
    
    # Render interactive document area window frame
    st.components.v1.html(workspace_html, height=img_h + 20, width=img_w + 20, scrolling=True)

    # --- EXPORT INTERFACE ---
    st.write("---")
    st.download_button(
        label="📥 Download Completed PDF",
        data=doc.write(),
        file_name="completed_form.pdf",
        mime="application/pdf",
        use_container_width=True
    )
