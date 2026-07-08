import streamlit as st

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🛠️ Custom Precision PDF Filler")
st.write("Tap EXACTLY on any black form line to type. Typing fields are now size-constrained perfectly!")

uploaded_file = st.file_uploader("Upload your document template:", type=["pdf"])

if uploaded_file is not None:
    import base64
    import fitz  # PyMuPDF
    
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    images_js_array = []
    for page_num in range(total_pages):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150) 
        img_data = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images_js_array.append(f"\"data:image/png;base64,{img_data}\"")
        
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    js_images_stream = ",\n".join(images_js_array)

    # --- PURE CANVAS DIRECT TAP INTERFACE WITH HARD MAXIMUM WIDTHS ---
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
            <img id="pdf-bg" src={images_js_array[0]} style="display: block; width: 100%; height: auto; user-select: none; -webkit-user-drag: none;" />
            <div id="text-layers-container" style="position: absolute; top:0; left:0; width:100%; height:100%;"></div>
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
        const layersContainer = document.getElementById('text-layers-container');

        let formMemory = [];
        let activeInput = null;

        function renderPageText() {{
            layersContainer.innerHTML = '';
            
            formMemory.forEach((entry, idx) => {{
                if (entry.pageIdx !== currentPage) return;
                
                const label = document.createElement('div');
                label.innerText = entry.text;
                label.style.position = 'absolute';
                label.style.left = `calc(${{entry.pctX * 100}}% + 2px)`;
                label.style.top = `calc(${{entry.pctY * 100}}% - 11px)`;
                label.style.fontSize = '12px';
                label.style.fontFamily = 'Helvetica, sans-serif';
                label.style.fontWeight = 'bold';
                label.style.color = '#0000FF';
                label.style.whiteSpace = 'nowrap';
                
                label.style.cursor = 'pointer';
                label.onclick = (e) => {{
                    e.stopPropagation();
                    formMemory.splice(idx, 1);
                    renderPageText();
                }};
                
                layersContainer.appendChild(label);
            }});
        }}

        layersContainer.addEventListener('click', function(e) {{
            if (activeInput) {{
                commitActiveInput();
                return;
            }}

            const rect = bgImg.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;
            
            const pctX = clickX / rect.width;
            const pctY = clickY / rect.height;

            const input = document.createElement('input');
            input.type = 'text';
            input.style.position = 'absolute';
            input.style.left = clickX + 'px';
            input.style.top = (clickY - 14) + 'px';
            
            // --- FIXED: BOUND BOX SIZE CONTROLS ---
            // Hard-locked max width limits prevent input box from expanding all over the sheet layout
            input.style.width = '180px';
            input.style.maxWidth = '220px';
            
            input.style.fontSize = '12px';
            input.style.fontFamily = 'Helvetica';
            input.style.color = '#0000FF';
            input.style.fontWeight = 'bold';
            input.style.border = 'none';
            input.style.borderBottom = '1.5px solid #0055FF';
            input.style.backgroundColor = 'rgba(255, 255, 200, 0.9)';
            input.style.outline = 'none';
            input.style.padding = '1px 2px';
            input.style.zIndex = '1000';
            
            layersContainer.appendChild(input);
            input.focus();
            
            activeInput = {{ element: input, pctX: pctX, pctY: pctY }};

            input.addEventListener('keydown', function(evt) {{
                if (evt.key === 'Enter') commitActiveInput();
            }});
            
            e.stopPropagation();
        }});

        function commitActiveInput() {{
            if (!activeInput) return;
            const val = activeInput.element.value.trim();
            if (val.length > 0) {{
                formMemory.push({{
                    text: val,
                    pctX: activeInput.pctX,
                    pctY: activeInput.pctY,
                    pageIdx: currentPage
                }});
            }}
            activeInput.element.remove();
            activeInput = null;
            renderPageText();
        }}

        function updatePageDisplay() {{
            if (activeInput) commitActiveInput();
            bgImg.src = pageImages[currentPage];
            pageIndicator.innerText = `Page ${{currentPage + 1}} of ${{totalPages}}`;
            renderPageText();
            
            prevBtn.disabled = (currentPage === 0);
            nextBtn.disabled = (currentPage === totalPages - 1);
        }}

        prevBtn.addEventListener('click', (e) => {{
            e.stopPropagation();
            if(currentPage > 0) {{ currentPage--; updatePageDisplay(); }}
        }});

        nextBtn.addEventListener('click', (e) => {{
            e.stopPropagation();
            if(currentPage < totalPages - 1) {{ currentPage++; updatePageDisplay(); }}
        }});

        updatePageDisplay();

        downloadBtn.addEventListener('click', async function(e) {{
            e.stopPropagation();
            if (activeInput) commitActiveInput();
            
            try {{
                const pdfDataBytes = Uint8Array.from(atob('{pdf_base64}'), c => c.charCodeAt(0));
                const pdfDoc = await PDFLib.PDFDocument.load(pdfDataBytes);
                const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.HelveticaBold);
                const pages = pdfDoc.getPages();
                
                for (let entry of formMemory) {{
                    const targetPage = pages[entry.pageIdx];
                    const {{ width, height }} = targetPage.getSize();
                    
                    const pdfX = entry.pctX * width;
                    const pdfY = height - (entry.pctY * height) - 3;

                    targetPage.drawText(entry.text, {{
                        x: pdfX,
                        y: pdfY,
                        size: 10, 
                        font: helveticaFont,
                        color: PDFLib.rgb(0, 0, 0.8)
                    }});
                }}

                const savedPdfBytes = await pdfDoc.save();
                const blob = new Blob([savedPdfBytes], {{ type: 'application/pdf' }});
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'form_completed.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }} catch (err) {{
                alert("Download Error: " + err.message);
            }}
        }});
    </script>
    """
    st.components.v1.html(filler_html, height=pix.height + 150, width=pix.width + 50, scrolling=True)
