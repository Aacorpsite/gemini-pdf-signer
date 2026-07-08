import streamlit as st

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🎯 Professional PDF Form Filler")
st.write("All artifact text noise has been wiped out. Checkboxes are now clean and ready for your 'X'!")

uploaded_file = st.file_uploader("Upload your document template:", type=["pdf"])

if uploaded_file is not None:
    import base64
    import fitz  # PyMuPDF
    
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    images_js_array = []
    widgets_html_by_page = {p: "" for p in range(total_pages)}
    
    for page_num in range(total_pages):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150) 
        img_data = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images_js_array.append(f'"data:image/png;base64,{img_data}"')
        
        img_w = pix.width
        img_h = pix.height
        
        for widget in page.widgets():
            r = widget.rect
            
            left_pct = (r.x0 / page.rect.width) * 100
            top_pct = (r.y0 / page.rect.height) * 100
            width_pct = ((r.x1 - r.x0) / page.rect.width) * 100
            height_pct = ((r.y1 - r.y0) / page.rect.height) * 100
            
            if height_pct > 3.0:
                height_pct = 2.5
            elif height_pct < 1.6:
                height_pct = 1.8
                
            f_id = widget.field_name.replace('"', '&quot;')
            
            raw_val = widget.field_value or ""
            cleaned_val = raw_val.strip()
            
            if len(cleaned_val) <= 3 and cleaned_val.lower() in ['f', 'ff', 't', 'on', 'off', '1', '0', 'yes', 'no']:
                current_val = ""
            else:
                current_val = raw_val

            widgets_html_by_page[page_num] += f"""
            <input type="text" data-field="{f_id}" data-page="{page_num}" value="{current_val}" 
                style="position: absolute; 
                       left: {left_pct}%; 
                       top: {top_pct}%; 
                       width: {width_pct}%; 
                       height: {height_pct}%; 
                       max-width: {width_pct}%; 
                       max-height: {height_pct}%;
                       box-sizing: border-box;
                       background-color: rgba(255, 235, 59, 0.22); 
                       border: 1px solid #ffc107; 
                       border-radius: 1px; 
                       font-size: 9px; 
                       font-family: Helvetica, sans-serif; 
                       font-weight: bold; 
                       color: #0000FF;
                       text-align: center;
                       padding: 0; 
                       margin: 0;
                       outline: none; 
                       z-index: 10; 
                       line-height: normal;
                       overflow: hidden;"
            />
            """

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    js_images_stream = ",\n".join(images_js_array)
    
    all_inputs_html = ""
    for p_idx, html_content in widgets_html_by_page.items():
        layer_visibility = "block" if p_idx == 0 else "none"
        all_inputs_html += f'<div class="page-layer" id="layer-{p_idx}" style="display: {layer_visibility}; position: absolute; top:0; left:0; width:100%; height:100%;">\n{html_content
