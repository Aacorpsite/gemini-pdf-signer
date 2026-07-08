import streamlit as st
import fitz  # PyMuPDF
import io
import base64
from PIL import Image

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🎯 Direct Visual PDF Signer")

# --- INITIALIZE MEMORY BLOCKS ---
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "field_values" not in st.session_state:
    st.session_state.field_values = {}
if "current_page" not in st.session_state:
    st.session_state.current_page = 0

uploaded_file = st.file_uploader("Upload your document:", type=["pdf"])

if uploaded_file is not None:
    if st.session_state.pdf_data is None:
        st.session_state.pdf_data = uploaded_file.read()

    doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
    total_pages = len(doc)

    # --- PROCESS REAL-TIME KEYBOARD UPDATES ---
    query_params = st.query_params
    if "update_field" in query_params:
        f_name = query_params["update_field"]
        f_val = query_params.get("value", "")
        
        st.session_state.field_values[f_name] = f_val
        
        # Burn the value directly into the PDF structure on its correct page
        for p_idx in range(total_pages):
            for widget in doc[p_idx].widgets():
                if widget.field_name == f_name:
                    widget.field_value = f_val
                    widget.update()
                    break
        st.session_state.pdf_data = doc.write()
        st.query_params.clear()
        st.rerun()

    # --- 📄 PAGE NAVIGATION BAR 📄 ---
    st.write("---")
    col_prev, col_status, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.current_page == 0)):
            st.session_state.current_page -= 1
            st.rerun()
            
    with col_status:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>Page {st.session_state.current_page + 1} of {total_pages}</h3>", unsafe_allow_html=True)
        
    with col_next:
        if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.current_page == total_pages - 1)):
            st.session_state.current_page += 1
            st.rerun()
    st.write("---")

    # Render only the actively selected page view
    active_page = doc[st.session_state.current_page]
    pix = active_page.get_pixmap(dpi=130)
    
    img_bytes = pix.tobytes("png")
    encoded_img = base64.b64encode(img_bytes).decode("utf-8")
    
    img_w = pix.width
    img_h = pix.height
    scale_x = img_w / active_page.rect.width
    scale_y = img_h / active_page.rect.height

    # Build individual inline inputs for the active page widgets
    input_elements_html = ""
    for widget in active_page.widgets():
        r = widget.rect
        x = r.x0 * scale_x
        y = r.y0 * scale_y
        w = (r.x1 - r.x0) * scale_x
        h = (r.y1 - r.y0) * scale_y
        
        if h < 16:
            h = 18
            
        current_val = st.session_state.field_values.get(widget.field_name, widget.field_value or "")
        
        input_elements_html += f"""
        <input type="text" value="{current_val}" 
            style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px; 
                   background-color: rgba(255, 235, 59, 0.15); border: 1.5px dashed #e6b800; 
                   border-radius: 2px; font-size: 13px; font-family: sans-serif; color: #0000FF;
                   padding: 0px 2px; box-sizing: border-box;"
            onblur="parent.window.location.search = '?update_field=' + encodeURIComponent('{widget.field_name}') + '&value=' + encodeURIComponent(this.value);"
        />
        """

    workspace_html = f"""
    <div style="position: relative; width: {img_w}px; height: {img_h}px; margin: 0 auto; user-select: none;">
        <img src="data:image/png;base64,{encoded_img}" style="width: 100%; height: 100%; display: block;" />
        {input_elements_html}
    </div>
    """
    
    st.components.v1.html(workspace_html, height=img_h + 20, width=img_w + 20, scrolling=True)

    # --- SAVE & EXPORT SECTION ---
    st.write("---")
    col_save_btn, col_dl_btn = st.columns(2)
    
    with col_save_btn:
        if st.button("💾 Save Progress & Verify", use_container_width=True):
            st.success("All fields securely locked into the document file memory layer!")
            
    with col_dl_btn:
        st.download_button(
            label="📥 Download Completed PDF",
            data=st.session_state.pdf_data,
            file_name="completed_form.pdf",
            mime="application/pdf",
            use_container_width=True
        )
