import streamlit as st

st.set_page_config(page_title="My Own Free PDF Filler", layout="wide")
st.title("🛠️ My Own Free PDF Filler")
st.write("Upload a PDF. Click anywhere directly on the page to type your text. When finished, hit Download.")

# Simple file uploader to feed the local browser application
uploaded_file = st.file_uploader("Upload your document template:", type=["pdf"])

if uploaded_file is not None:
    import base64
    import fitz  # PyMuPDF (used only to render the initial sharp layout pages)
    
    # Read the file data into a clean browser data string stream
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Handle multi-page documents safely
    total_pages = len(doc)
    page_num = st.number_input("Select Page", min_value=1, max_value=total_pages, value=1) - 1
    
    # Convert the selected page to a high-quality background image string
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    img_data = base64.b64encode(pix.tobytes("png")).decode("utf-8")
    
    # Pass the raw PDF bytes straight to the local browser engine
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    # --- THE CLIENT-SIDE INDESTRUCTIBLE FILLER ENGINE ---
    # This entire script runs directly inside your phone's memory. It cannot drop connection or lose data.
    filler_html = f"""
    <div id="wrapper" style="position: relative; max-width: 100%; overflow-x: auto; text-align: center; font-family: Arial, sans-serif;">
        <div style="margin-bottom: 15px;">
            <button id="downloadBtn" style="padding: 12px 24px; font-size: 16px; font-weight: bold; background-color: #00CC66; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">
                📥 Download Completed PDF
            </button>
        </div>
        
        <div id="canvas-container" style="position: relative; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ccc;">
            <img id="pdf-bg" src="data:image/png;base64,{img_data}" style="display: block; max-width: 100%; height: auto;" />
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"></script>

    <script>
        const canvasContainer = document.getElementById('canvas-container');
        const bgImg = document.getElementById('pdf-bg');
        const downloadBtn = document.getElementById('downloadBtn');
        
        // This array safely locks every piece of text you type into your phone's local active memory loop
        let typedEntries = [];
        let currentInput = null;

        // Capture direct phone finger taps perfectly right on the form lines
        canvasContainer.addEventListener('click', function(e) {{
            if (e.target !== bgImg && e.target !== canvasContainer) return;
            
            if (currentInput) {{
                commitCurrentInput();
            }}

            const rect = bgImg.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;
            
            // Calculate exact percentage scales to ensure typing scales beautifully on all screens
            const pctX = clickX / rect.width;
            const pctY = clickY / rect.height;

            // Spawn an interactive native overlay input field right under your finger tip
            const input = document.createElement('input');
            input.type = 'text';
            input.style.position = 'absolute';
            input.style.left = clickX + 'px';
            input.style.top = (clickY - 10) + 'px';
            input.style.fontSize = '14px';
            input.style.fontFamily = 'Helvetica';
            input.style.color = '#0000FF';
            input.style.border = '1px dashed #0055FF';
            input.style.backgroundColor = 'rgba(255, 255, 150, 0.4)';
            input.style.padding = '2px';
            input.style.outline = 'none';
            input.style.zIndex = '1000';
            
            canvasContainer.appendChild(input);
            input.focus();
            currentInput = {{ element: input, pctX: pctX, pctY: pctY }};

            // Force keyboard enter button to instantly save
            input.addEventListener('keydown', function(evt) {{
                if (evt.key === 'Enter') {{
                    commitCurrentInput();
                }}
            }});
        }});

        function commitCurrentInput() {{
            if (!currentInput) return;
            const text = currentInput.element.value.trim();
            if (text.length > 0) {{
                // Lock text metadata safely into memory arrays
                typedEntries.push({{
                    text: text,
                    pctX: currentInput.pctX,
                    pctY: currentInput.pctY,
                    pageIdx: {page_num}
                }});
                
                // Solidify the entry visually right over the document line
                const textLabel = document.createElement('div');
                textLabel.innerText = text;
                textLabel.style.position = 'absolute';
                textLabel.style.left = currentInput.element.style.left;
                textLabel.style.top = currentInput.element.style.top;
                textLabel.style.fontSize = '14px';
                textLabel.style.fontFamily = 'Helvetica';
                textLabel.style.color = '#0000FF';
                textLabel.style.pointerEvents = 'none';
                canvasContainer.appendChild(textLabel);
            }}
            currentInput.element.remove();
            currentInput = null;
        }}

        // --- MASTER DIRECT LOCAL WRITER AND SAVER ---
        downloadBtn.addEventListener('click', async function() {{
            if (currentInput) commitCurrentInput();
            
            try {{
                // Load the original raw document data bytes inside the browser engine sandbox
                const pdfDataBytes = Uint8Array.from(atob('{pdf_base64}'), c => c.charCodeAt(0));
                const pdfDoc = await PDFLib.PDFDocument.load(pdfDataBytes);
                const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.Helvetica);
                const pages = pdfDoc.getPages();

                // Directly map user coordinate entries back to raw vector space coordinates
                for (let entry of typedEntries) {{
                    const targetPage = pages[entry.pageIdx];
                    const {{ width, height }} = targetPage.getSize();
                    
                    const pdfX = entry.pctX * width;
                    // PDF coordinates measure from the bottom up, so we invert the height metric perfectly
                    const pdfY = height - (entry.pctY * height) - 3; 

                    targetPage.drawText(entry.text, {{
                        x: pdfX,
                        y: pdfY,
                        size: 11,
                        font: helveticaFont,
                        color: PDFLib.rgb(0, 0, 1) // Clean professional dark blue text stamp
                    }});
                }}

                // Generate file bytes dynamically right inside your local phone cache
                const savedPdfBytes = await pdfDoc.save();
                const blob = new Blob([savedPdfBytes], {{ type: 'application/pdf' }});
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'my_completed_form.pdf';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }} catch (err) {{
                alert("Error compilation layer: " + err.message);
            }}
        }});
    </script>
    """
    # Deploy the custom engine space iframe safely
    st.components.v1.html(filler_html, height=pix.height + 100, width=pix.width + 50, scrolling=True)
