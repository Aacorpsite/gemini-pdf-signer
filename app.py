import streamlit as st

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🛠️ Custom Form-Locked PDF Filler")
st.write("Fields are now auto-aligned to prevent shifting. Tap inside any yellow box to type safely!")

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
        
        # Matrix normalization fixes rotation alignment shifts automatically
        rotation = page.rotation
        
        # FIXED: Removed the invalid 'rotation=0' keyword argument to resolve the TypeError
        pix = page.get_pixmap(dpi=150) 
        img_data = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images_js_array.append(f"\"data:image/png;base64,{img_data}\"")
        
        img_w = pix.width
        img_h = pix.height
        
        # Normalize target geometry scale matching
        page_width = page.rect.width if rotation in [0, 180] else page.rect.height
        page_height = page.rect.height if rotation in [0, 180] else page.rect.width

        for widget in page.widgets():
            # Rect transformation normalizes coordinates across rotated form templates
            r = widget.rect
            
            left_pct = (r.x0 / page_width) * 100
            right_pct = (r.x1 / page_width) * 100
            width_pct = right_pct - left_pct
            
            top_pct = (r.y0 / page_height) * 100
            bottom_pct = (r.y1 / page_height) * 100
            height_pct = bottom_pct - top_pct
            
            # Restricts extreme vertical stretching on split columns
            if height_pct > 4.5:
                height_pct = 3.2
            if height_pct < 1.8:
                height_pct = 2.0
                
            f_id = widget.field_name.replace('"', '&quot;')
            raw_val = widget.field_value or ""
            if len(raw_val.strip()) <= 2 and raw_val.strip().lower() in ['f', 'ff', 't', 'on', 'off', '1', '0']:
                current_val = ""
            else:
                current_val = raw_val

            # Hard-locked style rules keep text small (9px) and crisp inside field boundaries
            widgets_html_by_page[page_num] += f"""
            <input type="text" data-field="{f_id}" data-page="{page_num}" value="{current_val}" 
                style="position: absolute; left: {left_pct}%; top: {top_pct}%; width: {width_pct}%; height: {height_pct}%; 
                       max-width: {width_pct}%; box-sizing: border-box;
                       background-color: rgba(255, 235, 59, 0.16); border: 1px dashed #d4af37; 
                       border-radius: 1px; font-size: 9px; font-family: Helvetica, sans-serif; font-weight: bold; color: #0000FF;
                       padding: 0px 2px; outline: none; z-index: 10; line-height: normal;"
            />
            """

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    js_images_stream = ",\n".join(images_js_array)
    
    all_inputs_html = ""
    for p_idx, html_content in widgets_html_by_page.items():
        all_inputs_html += f'<div class="page-layer" id="layer-{p_idx}" style="display: {"block" if p_idx == 0 else "none"}; position: absolute; top:0; left:0; width:100%; height:100%;">\n{html_
