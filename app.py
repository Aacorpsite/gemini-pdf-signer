import streamlit as st

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🛠️ Custom Form-Locked PDF Filler")
st.write("Tap directly inside any yellow highlighted box to type. Box boundaries and text sizes are locked perfectly!")

uploaded_file = st.file_uploader("Upload your document template:", type=["pdf"])

if uploaded_file is not None:
    import base64
    import fitz  # PyMuPDF
    
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    total_pages = len(doc)
    page_num = st.number_input("Select Page", min_value=1, max_value=total_pages, value=1) - 1
    
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    img_data = base64.b64encode(pix.tobytes("png")).decode("utf-8")
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    img_w = pix.width
    img_h = pix.height

    input_elements_html = ""
    for widget in page.widgets():
        r = widget.rect
        
        left_pct = (r.x0 / page.rect.width) * 100
        top_pct = (r.y0 / page.rect.height) * 100
        width_pct = ((r.x1 - r.x0) / page.rect.width) * 100
        height_pct = ((r.y1 - r.y0) / page.rect.height) * 100
        
        if height_pct < 2.0:
            height_pct = 2.2
            
        f_id = widget.field_name.replace('"', '&quot;')
        
        # --- FIXED: SQUASH DEFAULT PLACEHOLDER NOISE ---
        # If the backend PDF value contains random single character artifact noise, ignore it and keep the box clean and blank
        raw_val = widget.field_value or ""
        if len(raw_val.strip()) <= 2 and raw_val.strip().lower() in ['f', 'ff', 't', 'on', 'off', '1', '0']:
            current_val = ""
        else:
            current_val = raw_val

        # --- OPTIMIZED STYLING FOR COMPACT MOBIL SPACES ---
        # Smaller text (11px) prevents layout overflows on narrow lines
        input_elements_html += f"""
        <input type="text" data-field="{f_id}" value="{current_val}" 
            style="position: absolute; left: {left_pct}%; top: {top_pct}%; width: {width_pct}%; height: {height_pct}%; 
                   background-color: rgba(255, 235, 59, 0.22); border: 1px dashed #e6b800; 
                   border-radius: 1px; font-size: 11px; font-family: Helvetica, sans-serif; font-weight: bold; color: #0000FF;
                   padding: 0px 2px; box-sizing: border-box; outline: none; z-index: 10;"
        />
        """

    # --- RESPONSIVE CLIENT-SIDE LAYERING ENGINE ---
    filler_html = f"""
    <div id="wrapper" style="position: relative; max-width: 100%; text-align: center; font-family: Arial, sans-serif; margin: 0 auto;">
        <div style="margin-bottom: 15px;">
            <button id="downloadBtn" style="padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #00CC66; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">
                📥 Download Completed PDF
            </button>
        </div>
        
        <div id="canvas-container" style="position: relative; display: inline-block; width: 100%; max-width: {img_w}px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ccc; touch-action: manipulation;">
            <img id="pdf-bg" src="data:image/png;base64,{img_data}" style="display: block; width: 100%; height: auto; pointer-events: none;" />
            {input_elements_html}
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"></script>

    <script>
        const downloadBtn = document.getElementById('downloadBtn');

        downloadBtn.addEventListener('click', async function() {{
            try {{
                const pdfDataBytes = Uint8Array.from(atob('{pdf_base64}'), c => c.charCodeAt(0));
                const pdfDoc = await PDFLib.PDFDocument.load(pdfDataBytes);
                const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.HelveticaBold);
                const pages = pdfDoc.getPages();
                const targetPage = pages[{page_num}];
                const {{ width, height }} = targetPage.getSize();
                
                const inputs = document.querySelectorAll('#canvas-container input');
                
                for (let input of inputs) {{
                    const fieldName = input.getAttribute('data-field');
                    const textValue = input.value.trim();
                    
                    if (textValue.length > 0) {{
                        const leftPct = parseFloat(input.style.left) / 100;
                        const topPct = parseFloat(input.style.top) / 100;
                        
                        const pdfX = leftPct * width;
                        // Slightly lower text offset baseline to align text crisply on the physical lines
                        const pdfY = height - (topPct * height) - 10; 

                        targetPage.drawText(textValue, {{
                            x: pdfX,
                            y: pdfY,
                            size: 9, // Outputs slightly smaller to perfectly match long addresses
                            font: helveticaFont,
                            color: PDFLib.rgb(0, 0, 0.8) // Dark professional blue
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
                document.body.removeChild(link);
            }} catch (err) {{
                alert("Processing Error: " + err.message);
            }}
        }});
    </script>
    """
    st.components.v1.html(filler_html, height=img_h + 100, width=img_w + 50, scrolling=True)
