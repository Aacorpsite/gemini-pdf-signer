import streamlit as st

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🛠️ Custom Form-Locked PDF Filler")
st.write("Tap directly inside any bounded yellow line box to type. Every box is constrained perfectly to its own form line width!")

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

    # Gather precise interactive coordinates from the embedded PDF widgets
    img_w = pix.width
    img_h = pix.height
    scale_x = img_w / page.rect.width
    scale_y = img_h / page.rect.height

    input_elements_html = ""
    for widget in page.widgets():
        r = widget.rect
        x = r.x0 * scale_x
        y = r.y0 * scale_y
        w = (r.x1 - r.x0) * scale_x
        h = (r.y1 - r.y0) * scale_y
        
        # Keep structural height padding safe for mobile fingertips
        if h < 16:
            h = 18
            
        # Unique field tracking anchor
        f_id = widget.field_name.replace('"', '&quot;')
        current_val = widget.field_value or ""

        # FORCE STRICT WIDTH LIMITS AND REMOVE STRETCHING
        input_elements_html += f"""
        <input type="text" data-field="{f_id}" value="{current_val}" 
            style="position: absolute; left: {x}px; top: {y}px; width: {w}px; height: {h}px; 
                   max-width: {w}px; min-width: {w}px; /* Hard-lock the width explicitly */
                   background-color: rgba(255, 235, 59, 0.08); border: 1px dashed #ffc107; 
                   border-radius: 2px; font-size: 13px; font-family: Helvetica, sans-serif; color: #0000FF;
                   padding: 0px 4px; box-sizing: border-box; outline: none;"
        />
        """

    # --- CLIENT-SIDE ENGINE WITH WIDTH ENFORCEMENT ---
    filler_html = f"""
    <div id="wrapper" style="position: relative; max-width: 100%; text-align: center; font-family: Arial, sans-serif;">
        <div style="margin-bottom: 15px;">
            <button id="downloadBtn" style="padding: 12px 24px; font-size: 16px; font-weight: bold; background-color: #00CC66; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">
                📥 Download Completed PDF
            </button>
        </div>
        
        <div id="canvas-container" style="position: relative; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ccc;">
            <img id="pdf-bg" src="data:image/png;base64,{img_data}" style="display: block; max-width: 100%; height: auto;" />
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
                const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.Helvetica);
                const pages = pdfDoc.getPages();
                const targetPage = pages[{page_num}];
                
                // Read values from the hard-bounded input fields right inside your browser
                const inputs = document.querySelectorAll('#canvas-container input');
                
                for (let input of inputs) {{
                    const fieldName = input.getAttribute('data-field');
                    const textValue = input.value.trim();
                    
                    if (textValue.length > 0) {{
                        // Read the precise relative layout positions natively from the page widget fields
                        const styleLeft = parseFloat(input.style.left);
                        const styleTop = parseFloat(input.style.top);
                        
                        const {{ width, height }} = targetPage.getSize();
                        const pdfX = (styleLeft / {img_w}) * width;
                        const pdfY = height - ((styleTop / {img_h}) * height) - 11; // Align beautifully down onto baseline

                        targetPage.drawText(textValue, {{
                            x: pdfX,
                            y: pdfY,
                            size: 10,
                            font: helveticaFont,
                            color: PDFLib.rgb(0, 0, 1)
                        }});
                    }}
                }}

                const savedPdfBytes = await pdfDoc.save();
                const blob = new Blob([savedPdfBytes], {{ type: 'application/pdf' }});
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'form_completed_locked.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }} catch (err) {{
                alert("Compilation processing error: " + err.message);
            }}
        }});
    </script>
    """
    st.components.v1.html(filler_html, height=pix.height + 100, width=pix.width + 50, scrolling=True)
