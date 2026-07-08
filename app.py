import streamlit as st
import fitz  # PyMuPDF
import io
import base64
from PIL import Image

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🎯 Direct Visual PDF Signer")
st.write("Tap directly inside any yellow dashed box to type. Press 'Done' or 'Enter' on your keyboard to lock it in.")

# --- PERSISTENT STORAGE LAYER ---
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

    # --- MOBILE-KEYBOARD SAVE TRIGGER ---
    query_params = st.query_params
    if "update_field" in query_params:
        f_name = query_params["update_field"]
        f_val = query_params.get("value", "")
        
        st.session_state.field_values[f_name] = f_val
        
        # Burn value directly into the PDF structure on its correct page layer
        for p_idx in range(total_pages):
            for widget in doc[p_idx].widgets():
                if widget.field_name == f_name:
                    widget.field_value = f_val
                    widget.update()
                    break
        st.session_state.pdf_data = doc.write()
        st.query_params.clear()
        st.rerun()

    # --- PAGE NAVIGATION ---
    if total_pages > 1:
        st.write("---")
        col_prev, col_status, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️ Previous Page", use_container_width=True, disabled=(st.session_state.current_page == 0)):
                st.session_state.current_page -= 1
                st.rerun()
        with col_status:
            st.markdown(f"<h4 style='text-align: center; margin: 0;'>Page {st.session_state.current_page + 1} of {total_pages}</h4>", unsafe_allow_html=True)
        with col_next:
            if st.button("Next Page ➡️", use_container_width=True, disabled=(st.session_state.current_page == total_pages - 1)):
                st.session_state.current_page += 1
                st.rerun()
        st.write("---")

    # Render current page view frame assets
    page = doc[st.session_state.current_page]
    pix = page.get_pixmap(dpi=140)
    
    img_bytes = pix.tobytes("png")
    encoded_img = base64.b64encode(img_bytes).decode("utf-8")
    
    img_w = pix.width
    img_h = pix.height
    scale_x = img_w / page.rect.width
    scale_y = img_h / page.rect.height

    # Build clean interactive typing boxes exactly over form shapes
    input_elements_html = ""
    for widget in page.widgets():
        r = widget.rect
        x = r.x0 * scale_x
        y = r.y0 * scale_y
        w = (r.x1 - r.x0) * scale_x
        h = (r.y1 - r.y0) * scale_y
        
        if h < 16:
            h = 18
            
        current_val = st.session_state.field_values.get(widget.field_name, widget.field_value or "")
        
        # Uses 'onchange' to ensure typing saves instantly when hitting return/done on mobile
        input_elements_html += f"""
        <input type="text" value="{current_val}" 
            style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px; 
                   background-color: rgba(255, 235, 59, 0.12); border: 1.5px dashed #ffc107; 
                   border-radius: 2px; font-size: 13px; font-family: sans-serif; color: #0000FF;
                   padding: 0px 2px; box-sizing: border-box;"
            onchange="parent.window.location.search = '?update_field=' + encodeURIComponent('{widget.field_name}') + '&value=' + encodeURIComponent(this.value);"
        />
        """

    workspace_html = f"""
    <div style="position: relative; width: {img_w}px; height: {img_h}px; margin: 0 auto; user-select: none;">
        <img src="data:image/png;base64,{encoded_img}" style="width: 100%; height: 100%; display: block;" />
        {input_elements_html}
    </div>
    """
    
    st.components.v1.html(workspace_html, height=img_h + 20, width=img_w + 20, scrolling=True)

    # --- DOWNLOAD EXPORT CONTROLLER ---
    st.write("---")
    st.download_button(
        label="📥 Download Completed PDF",
        data=st.session_state.pdf_data,
        file_name="completed_application.pdf",
        mime="application/pdf",
        use_container_width=True
    )
