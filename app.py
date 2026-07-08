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
        images_js_array.append(f"\"data:image/png;base64,{img_data}\"")
        
        img_w = pix.width
        img_h = pix.height
        
        for widget in page.widgets():
            r = widget.rect
            
            left_pct = (r.x0 / page.rect.width) * 100
            top_pct = (r.y0 / page.rect.height) * 100
            width_pct = ((r.x1 - r.x0) / page.rect.width) * 100
            height_pct = ((r.y1 - r.y0) / page.rect.height) * 100
            
            # Keep height metrics safe from overlapping
            if height_pct > 3.0:
                height_pct = 2.5
            elif height_pct < 1.6:
                height_pct = 1.8
                
            f_id = widget.field_name.replace('"', '&quot;')
            
            # --- FIXED: FORCE WIPE SINGLE LETTER CHECKBOX NOISE ---
            raw_val = widget.field_value or ""
            cleaned_val = raw_val.strip()
            
            # If it's an internal placeholder string ('f', 'ff', 't', 'yes', 'no'), force it completely empty
            if len(cleaned_val) <= 3 and cleaned_val.lower() in ['f', 'ff', 't', 'on', 'off', '1', '0', 'yes', 'no']:
                current_val = ""
            else:
                current_val = raw_val

            # STYLE FIX: text-align centers your 'X' markers directly inside the small checkbox frames
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
                       text-align: center; /* Centers X marks cleanly inside boxes */
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
        all_inputs_html += f'<div class="page-layer" id="layer-{p_idx}" style="display: {layer_visibility}; position: absolute; top:0; left:0; width:100%; height:100%;">\n{html_content}\n</div>'

    # --- CLIENT INTERFACE CANVAS ---
    filler_html = f"""
    <div id="wrapper" style="position: relative; max-width: 100%; text-align: center; font-family: Arial, sans-serif; margin: 0 auto;">
        
        <div style="margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">
            <button id="prevBtn" style="padding: 11px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">⬅️ Previous Page</button>
            <span id="pageIndicator" style="font-size: 16px; font-weight: bold; min-width: 100px;">Page 1 of {total_pages}</span>
            <button id="nextBtn" style="padding: 11px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">Next Page ➡️</button>
        </div>

        <div style="margin-bottom: 15px;">
            <button id="downloadBtn" style="padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #00CC66; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">
                📥 Download Completed PDF
            </button>
        </div>
        
        <div id="canvas-container" style="position: relative; display: inline-block; width: 100%; max-width: {pix.width}px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ccc; touch-action: manipulation;">
            <img id="pdf-bg" src={images_js_array[0]} style="display: block; width: 100%; height: auto; pointer-events: none; user-select: none;" />
            <div id="inputs-viewport" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
                {all_inputs_html}
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"></script>

    <script>
        const pageImages = [{js_images_stream}];
        let currentPage = 0;
        const totalPages = {total_pages};

        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const pageIndicator = document.getElementById('pageIndicator');
        const bgImg = document.getElementById('pdf-bg');
        const downloadBtn = document.getElementById('downloadBtn');

        function updatePageDisplay() {{
            bgImg.src = pageImages[currentPage];
            pageIndicator.innerText = `Page ${{currentPage + 1}} of ${{totalPages}}`;
            
            for(let i=0; i<totalPages; i++) {{
                const layer = document.getElementById(`layer-${{i}}`);
                if(layer) {{
                    layer.style.display = (i === currentPage) ? "block" : "none";
                }}
            }}
            
            prevBtn.disabled = (currentPage === 0);
            nextBtn.disabled = (currentPage === totalPages - 1);
        }}

        prevBtn.addEventListener('click', () => {{
            if(currentPage > 0) {{ currentPage--; updatePageDisplay(); }}
        }});

        nextBtn.addEventListener('click', () => {{
            if(currentPage < totalPages - 1) {{ currentPage++; updatePageDisplay(); }}
        }});

        updatePageDisplay();

        downloadBtn.addEventListener('click', async function() {{
            try {{
                const pdfDataBytes = Uint8Array.from(atob('{pdf_base64}'), c => c.charCodeAt(0));
                const pdfDoc = await PDFLib.PDFDocument.load(pdfDataBytes);
                const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.HelveticaBold);
                const pages = pdfDoc.getPages();
                
                const inputs = document.querySelectorAll('#canvas-container input');
                
                for (let input of inputs) {{
                    const fieldName = input.getAttribute('data-field');
                    const pageIdx = parseInt(input.getAttribute('data-page'));
                    const textValue = input.value.trim();
                    
                    if (textValue.length > 0) {{
                        const targetPage = pages[pageIdx];
                        const {{ width, height }} = targetPage.getSize();
                        
                        const leftPct = parseFloat(input.style.left) / 100;
                        const topPct = parseFloat(input.style.top) / 100;
                        const widthPct = parseFloat(input.style.width) / 100;
                        
                        // Center horizontal alignment execution for check marks
                        let pdfX = leftPct * width;
                        if (textValue.toLowerCase() === 'x' && (widthPct * width) < 25) {{
                            pdfX = (leftPct * width) + ((widthPct * width) / 2) - 3.5;
                        }}
                        
                        const pdfY = height - (topPct * height) - 8.5; 

                        targetPage.drawText(textValue, {{
                            x: pdfX,
                            y: pdfY,
                            size: 9, 
                            font: helveticaFont,
                            color: PDFLib.rgb(0, 0, 0.75)
                        }});
                    }}
                }}

                const savedPdfBytes = await pdfDoc.save();
                const blob = new Blob([savedPdfBytes], {{ type: 'application/pdf' }});
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'housing_application_completed.pdf';
                document.body.appendChild(link);
                link.click();
                document
