import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image

st.set_page_config(page_title="Reliable PDF Filler", layout="wide")
st.title("📝 Clean & Reliable PDF Filler")
st.write("Type your information into the fields below, click 'Apply Changes', and download your finished copy.")

# --- PERSISTENT STORAGE LAYER ---
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
    
    # Simple Page Navigation
    if total_pages > 1:
        page_num = st.number_input("Select Form Page", min_value=1, max_value=total_pages, value=1) - 1
    else:
        page_num = 0

    page = doc[page_num]
    widgets = list(page.widgets())

    # Create two clean columns: Form Fields on Left, Live PDF Preview on Right
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🖋️ Form Fields")
        if widgets:
            # Generate real, native typing boxes for every field found on this page
            for widget in widgets:
                field_label = widget.field_name if widget.field_name else f"Line Box ({widget.xref})"
                current_saved_val = st.session_state.field_values.get(widget.field_name, widget.field_value or "")
                
                # Native Streamlit input boxes always work flawlessly on phone keyboards
                st.text_input(
                    f"👉 {field_label}", 
                    value=current_saved_val, 
                    key=f"native_box_{widget.field_name}_{widget.xref}"
                )

            # One solid save button to lock all inputs into the actual file memory
            if st.button("💾 Apply & Lock Changes", use_container_width=True):
                for widget in widgets:
                    user_typed_value = st.session_state[f"native_box_{widget.field_name}_{widget.xref}"]
                    st.session_state.field_values[widget.field_name] = user_typed_value
                    widget.field_value = user_typed_value
                    widget.update()
                
                st.session_state.pdf_data = doc.write()
                st.success("Changes permanently saved! Ready to download.")
                st.rerun()
        else:
            st.info("No interactive form fields found on this page.")

    with col2:
        st.subheader("👁️ Live Preview")
        # Render the current state of the document visually
        view_doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
        pix = view_doc[page_num].get_pixmap(dpi=120)
        st.image(pix.tobytes("png"), use_container_width=True)

    # --- RELIABLE EXPORT AREA ---
    st.write("---")
    st.download_button(
        label="📥 Download Finished PDF",
        data=st.session_state.pdf_data,
        file_name="completed_and_saved_form.pdf",
        mime="application/pdf",
        use_container_width=True
    )
