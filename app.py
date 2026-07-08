import streamlit as st

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🎯 Professional PDF Form Filler")
st.write("Font sizes now scale down automatically to prevent text like email addresses from being cut off!")

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

            # FIXED ENGINE: The adjustFontSize function recalculates size on every single character keystroke
            widgets_html_by_page[page_num] += f"""
            <input type="text" data-field="{f_id}" data-page="{page_num}" value="{current_val}" 
                oninput="if(window.adjustFontSize) {{ window.adjustFontSize(this); }} else {{ this.style.fontSize = this.value.length > 20 ? '6px' : (this.value.length > 12 ? '7.5px' : '10px'); }}"
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
                       font-size: 10px; 
                       font-family: Helvetica, sans-serif; 
                       font-weight: bold; 
                       color: #0000FF;
                       text-align: left;
                       padding: 0px 2px; 
                       margin: 0;
                       outline: none; 
                       z-index: 10; 
                       line-height: normal;"
            />
            """

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    js_images_stream = ",\n".join(images_js_array)
    
    all_inputs_html = ""
    for p_idx, html_content in widgets_html_by_page.items():
        if p_idx == 0:
            layer_visibility = "block"
        else:
            layer_visibility = "none"
            
        all_inputs_html += '<div class="page-layer" id="layer-' + str(p_idx) + '" style="display: ' + layer_visibility + '; position: absolute; top:0; left:0; width:100%; height:100%;">\n' + html_content + '\n</div>'

    # --- RAW TEMPLATE STREAM BLOCK ---
    raw_template = r"""
    <div id="wrapper" style="position: relative; max-width: 100%; text-align: center; font-family: Arial, sans-serif; margin: 0 auto;">
        
        <div style="margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">
            <button id="prevBtn" style="padding: 11px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">⬅️ Previous Page</button>
            <span id="pageIndicator" style="font-size: 16px; font-weight: bold; min-width: 100px;">Page 1 of __TOTAL_PAGES__</span>
            <button id="nextBtn" style="padding: 11px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">Next Page ➡️</button>
        </div>

        <div style="margin-bottom: 15px;">
            <button id="downloadBtn" style="padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #00CC66; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">
                📥 Download Completed PDF
            </button>
        </div>
        
        <div id="canvas-container" style="position: relative; display: inline-block; width: 100%; max-width: __MAX_WIDTH__px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ccc; touch-action: manipulation;">
            <img id="pdf-bg" src='__FIRST_PAGE_IMG__' style="display: block; width: 100%; height: auto; pointer-events: none; user-select: none;" />
            <div id="inputs-viewport" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
                __ALL_INPUTS_HTML__
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"></script>

    <script>
        window.adjustFontSize = function(input) {
            let size = 10;
            input.style.fontSize = size + "px";
            // Dynamically scale down font until the text scrolls back inside its container width boundaries
            while (input.scrollWidth > input.clientWidth && size > 5) {
                size -= 0.5;
                input.style.fontSize = size + "px";
            }
        };

        const pageImages = [__IMAGES_JS_STREAM__];
        let currentPage = 0;
        const totalPages = __TOTAL_PAGES__;

        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const pageIndicator = document.getElementById('pageIndicator');
        const bgImg = document.getElementById('pdf-bg');
        const downloadBtn = document.getElementById('downloadBtn');

        function updatePageDisplay() {
            bgImg.src = pageImages[currentPage];
            pageIndicator.innerText = "Page " + (currentPage + 1) + " of " + totalPages;
            
            for(let i=0; i<totalPages; i++) {
                const layer = document.getElementById("layer-" + i);
                if(layer) {
                    layer.style.display = (i === currentPage) ? "block" : "none";
                }
            }
            
            prevBtn.disabled = (currentPage === 0);
            nextBtn.disabled = (currentPage === totalPages - 1);
            
            // Trigger auto-scaling check for existing data on display switch
            setTimeout(() => {
                document.querySelectorAll('#canvas-container input').forEach(el => {
                    if (window.adjustFontSize) window.adjustFontSize(el);
                });
            }, 50);
        }

        prevBtn.addEventListener('click', () => {
            if(currentPage > 0) { currentPage--; updatePageDisplay(); }
        });

        nextBtn.addEventListener('click', () => {
            if(currentPage < totalPages - 1) { currentPage++; updatePageDisplay(); }
        });

        // Run initial configuration sync
        setTimeout(() => {
            document.querySelectorAll('#canvas-container input').forEach(el => {
                if (window.adjustFontSize) window.adjustFontSize(el);
            });
        }, 300);

        updatePageDisplay();

        downloadBtn.addEventListener('click', async function() {
            try {
                const pdfDataBytes = Uint8Array.from(atob('__PDF_BASE64__'), c => c.charCodeAt(0));
                const pdfDoc = await PDFLib.PDFDocument.load(pdfDataBytes);
                const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.HelveticaBold);
                const pages = pdfDoc.getPages();
                
                const inputs = document.querySelectorAll('#canvas-container input');
                
                for (let input of inputs) {
                    const fieldName = input.getAttribute('data-field');
                    const pageIdx = parseInt(input.getAttribute('data-page'));
                    const textValue = input.value.trim();
                    
                    if (textValue.length > 0) {
                        const targetPage = pages[pageIdx];
                        const sizeMetrics = targetPage.getSize();
                        const width = sizeMetrics.width;
                        const height = sizeMetrics.height;
                        
                        const leftPct = parseFloat(input.style.left) / 100;
                        const topPct = parseFloat(input.style.top) / 100;
                        const widthPct = parseFloat(input.style.width) / 100;
                        
                        let pdfX = leftPct * width;
                        
                        if (textValue.toLowerCase() === 'x' && (widthPct * width) < 25) {
                            pdfX = (leftPct * width) + ((widthPct * width) / 2) - 3.5;
                        }
                        
                        const pdfY = height - (topPct * height) - 8.5; 

                        // Calculate matching crisp print dimensions based on active layout font sizes
                        let computedFontSize = parseFloat(input.style.fontSize) || 10;
                        let printSize = computedFontSize * 0.95; 
                        if (printSize < 5.5) printSize = 5.5;

                        targetPage.drawText(textValue, {
                            x: pdfX,
                            y: pdfY,
                            size: printSize, 
                            font: helveticaFont,
                            color: PDFLib.rgb(0, 0, 0.75)
                        });
                    }
                }

                const savedPdfBytes = await pdfDoc.save();
                const blob = new Blob([savedPdfBytes], { type: 'application/pdf' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'housing_application_completed.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } catch (err) {
                alert("Processing Error: " + err.message);
            }
        });
    </script>
    """
    
    filler_html = raw_template.replace("__TOTAL_PAGES__", str(total_pages))
    filler_html = filler_html.replace("__MAX_WIDTH__", str(pix.width))
    filler_html = filler_html.replace("__FIRST_PAGE_IMG__", images_js_array[0].strip('"'))
    filler_html = filler_html.replace("__ALL_INPUTS_HTML__", all_inputs_html)
    filler_html = filler_html.replace("__IMAGES_JS_STREAM__", js_images_stream)
    filler_html = filler_html.replace("__PDF_BASE64__", pdf_base64)

    st.components.v1.html(filler_html, height=img_h + 150, width=img_w + 50, scrolling=True)
