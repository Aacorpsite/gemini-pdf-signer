import streamlit as st

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🛠️ Custom Form-Locked PDF Filler")
st.write("Fill out all pages smoothly. Everything saves locally automatically without losing data when switching pages!")

uploaded_file = st.file_uploader("Upload your document template:", type=["pdf"])

if uploaded_file is not None:
    import base64
    import fitz  # PyMuPDF
    
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    # Pre-render every page to base64 images so the user can switch pages locally without hitting the server
    images_js_array = []
    widgets_html_by_page = {p: "" for p in range(total_pages)}
    
    for page_num in range(total_pages):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_data = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images_js_array.append(f"\"data:image/png;base64,{img_data}\"")
        
        img_w = pix.width
        img_h = pix.height
        scale_x = img_w / page.rect.width
        scale_y = img_h / page.rect.height
        
        for widget in page.widgets():
            r = widget.rect
            left_pct = (r.x0 / page.rect.width) * 100
            top_pct = (r.y0 / page.rect.height) * 100
            width_pct = ((r.x1 - r.x0) / page.rect.width) * 100
            height_pct = ((r.y1 - r.y0) / page.rect.height) * 100
            
            if height_pct < 2.0:
                height_pct = 2.2
                
            f_id = widget.field_name.replace('"', '&quot;')
            raw_val = widget.field_value or ""
            if len(raw_val.strip()) <= 2 and raw_val.strip().lower() in ['f', 'ff', 't', 'on', 'off', '1', '0']:
                current_val = ""
            else:
                current_val = raw_val

            # FIXED: Font sizes shrunk to 10px, line-height locked, padding tight to ensure nothing overflows the lines
            widgets_html_by_page[page_num] += f"""
            <input type="text" data-field="{f_id}" data-page="{page_num}" value="{current_val}" 
                style="position: absolute; left: {left_pct}%; top: {top_pct}%; width: {width_pct}%; height: {height_pct}%; 
                       background-color: rgba(255, 235, 59, 0.15); border: 1px solid #e6b800; 
                       border-radius: 1px; font-size: 10px; font-family: Helvetica, sans-serif; font-weight: bold; color: #0000FF;
                       padding: 0px 2px; box-sizing: border-box; outline: none; z-index: 10; line-height: 10px;"
            />
            """

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    js_images_stream = ",\n".join(images_js_array)
    
    # Flatten all widget layers into a single client-side memory layout
    all_inputs_html = ""
    for p_idx, html_content in widgets_html_by_page.items():
        all_inputs_html += f'<div class="page-layer" id="layer-{p_idx}" style="display: {"block" if p_idx == 0 else "none"}; position: absolute; top:0; left:0; width:100%; height:100%;">\n{html_content}\n</div>'

    # --- INDESTRUCTIBLE LOCAL MULTI-PAGE CANVAS ENGINE ---
    filler_html = f"""
    <div id="wrapper" style="position: relative; max-width: 100%; text-align: center; font-family: Arial, sans-serif; margin: 0 auto;">
        
        <div style="margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">
            <button id="prevBtn" style="padding: 10px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">⬅️ Previous Page</button>
            <span id="pageIndicator" style="font-size: 16px; font-weight: bold; min-width: 100px;">Page 1 of {total_pages}</span>
            <button id="nextBtn" style="padding: 10px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">Next Page ➡️</button>
        </div>

        <div style="margin-bottom: 15px;">
            <button id="downloadBtn" style="padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #00CC66; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">
                📥 Download Completed PDF
            </button>
        </div>
        
        <div id="canvas-container" style="position: relative; display: inline-block; width: 100%; max-width: {pix.width}px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ccc; touch-action: manipulation;">
            <img id="pdf-bg" src={images_js_array[0]} style="display: block; width: 100%; height: auto; pointer-events: none;" />
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

        // Handle page updates fully inside the local layout view
        function updatePageDisplay() {{
            bgImg.src = pageImages[currentPage];
            pageIndicator.innerText = `Page ${{currentPage + 1}} of ${{totalPages}}`;
            
            // Show only the inputs belonging to the active page layer
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

        // Initialize state configuration rules
        updatePageDisplay();

        downloadBtn.addEventListener('click', async function() {{
            try {{
                const pdfDataBytes = Uint8Array.from(atob('{pdf_base64}'), c => c.charCodeAt(0));
                const pdfDoc = await PDFLib.PDFDocument.load(pdfDataBytes);
                const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.HelveticaBold);
                const pages = pdfDoc.getPages();
                
                // Scan across every input line from all page layers stored in browser cache
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
                        
                        const pdfX = leftPct * width;
                        const pdfY = height - (topPct * height) - 9; // Beautiful alignment on document lines

                        targetPage.drawText(textValue, {{
                            x: pdfX,
                            y: pdfY,
                            size: 8.5, // Crisp font output scale to handle long names/addresses perfectly
                            font: helveticaFont,
                            color: PDFLib.rgb(0, 0, 0.75)
                        }});
                    }}
                }}

                const savedPdfBytes = await pdfDoc.save();
                const blob = new Blob([savedPdfBytes], {{ type: 'application/pdf' }});
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'housing_application_filled.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }} catch (err) {{
                alert("Processing Error: " + err.message);
            }}
        }});
    </script>
    """
    st.components.v1.html(filler_html, height=pix.height + 150, width=pix.width + 50, scrolling=True)
