import streamlit as st
import base64

st.set_page_config(page_title="Professional PDF Filler", layout="wide")
st.title("🎯 Professional PDF Form Filler")
st.write("Tap text fields to type naturally. Checkboxes toggle automatically with a single tap!")

uploaded_file = st.file_uploader("Upload your document template:", type=["pdf"])

if uploaded_file is not None:
    import fitz  # PyMuPDF
    
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    images_js_array = []
    widgets_html_by_page = {}
    for p in range(total_pages):
        widgets_html_by_page[p] = ""
    
    for page_num in range(total_pages):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150) 
        img_data = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        images_js_array.append('"' + "data:image/png;base64," + img_data + '"')
        
        img_w = pix.width
        img_h = pix.height
        
        for widget in page.widgets():
            r = widget.rect
            
            left_pct = (r.x0 / page.rect.width) * 100
            top_pct = (r.y0 / page.rect.height) * 100
            width_pct = ((r.x1 - r.x0) / page.rect.width) * 100
            height_pct = ((r.y1 - r.y0) / page.rect.height) * 100
            
            # Strict height clipping keeps rows from bleeding down over form labels
            if height_pct > 2.8:
                height_pct = 2.2
            elif height_pct < 1.5:
                height_pct = 1.7
                
            f_id = widget.field_name.replace('"', '&quot;')
            f_id_lower = f_id.lower()
            
            raw_val = widget.field_value or ""
            cleaned_val = raw_val.strip()
            
            if len(cleaned_val) <= 3 and cleaned_val.lower() in ['f', 'ff', 't', 'on', 'off', '1', '0', 'yes', 'no']:
                current_val = ""
            else:
                current_val = raw_val

            # Differentiate square checkbox fields from rectangular numerical input boxes
            aspect_ratio = width_pct / height_pct if height_pct > 0 else 1
            is_numeric_word = "year" in f_id_lower or "month" in f_id_lower or "date" in f_id_lower or "phone" in f_id_lower

            if width_pct < 4.5 and not is_numeric_word and aspect_ratio < 1.6:
                widgets_html_by_page[page_num] += '<div data-field="' + f_id + '" data-page="' + str(page_num) + '" data-type="checkbox" onclick="if(window.toggleCheck) { window.toggleCheck(this); }" style="position: absolute; left: ' + str(left_pct) + '%; top: ' + str(top_pct) + '%; width: ' + str(width_pct) + '%; height: ' + str(height_pct) + '%; max-width: ' + str(width_pct) + '%; max-height: ' + str(height_pct) + '%; box-sizing: border-box; background-color: rgba(255, 235, 59, 0.25); border: 1px solid #ffc107; border-radius: 1px; font-size: 10px; font-family: Helvetica, sans-serif; font-weight: bold; color: #0000FF; text-align: center; display: flex; align-items: center; justify-content: center; cursor: pointer; user-select: none; z-index: 10; line-height: 10px;">' + current_val + '</div>\n'
            else:
                widgets_html_by_page[page_num] += '<input type="text" data-field="' + f_id + '" data-page="' + str(page_num) + '" data-type="text" value="' + current_val + '" oninput="if(window.adjustFontSize) { window.adjustFontSize(this); }" style="position: absolute; left: ' + str(left_pct) + '%; top: ' + str(top_pct) + '%; width: ' + str(width_pct) + '%; height: ' + str(height_pct) + '%; max-width: ' + str(width_pct) + '%; max-height: ' + str(height_pct) + '%; box-sizing: border-box; background-color: rgba(255, 235, 59, 0.22); border: 1px solid #ffc107; border-radius: 1px; font-size: 10px; font-family: Helvetica, sans-serif; font-weight: bold; color: #0000FF; text-align: left; padding: 0px 2px; margin: 0; outline: none; z-index: 10;" />\n'

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    js_images_stream = ",\n".join(images_js_array)
    
    all_inputs_html = ""
    for p_idx, html_content in widgets_html_by_page.items():
        layer_visibility = "block" if p_idx == 0 else "none"
        all_inputs_html += '<div class="page-layer" id="layer-' + str(p_idx) + '" style="display: ' + layer_visibility + '; position: absolute; top:0; left:0; width:100%; height:100%;">\n' + html_content + '\n</div>'

    # --- FIXED: LINE-BY-LINE CONCATENATION LIST ---
    # Assembling the UI using standard text lines guarantees Python will compile it cleanly without string literal errors
    ui_lines = [
        '<div id="wrapper" style="position: relative; max-width: 100%; text-align: center; font-family: Arial, sans-serif; margin: 0 auto;">',
        '    <div style="margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">',
        '        <button id="prevBtn" style="padding: 11px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">⬅️ Previous Page</button>',
        '        <span id="pageIndicator" style="font-size: 16px; font-weight: bold; min-width: 100px;">Page 1 of __TOTAL_PAGES__</span>',
        '        <button id="nextBtn" style="padding: 11px; font-weight: bold; background-color: #0055FF; color: white; border: none; border-radius: 4px; flex: 1;">Next Page ➡️</button>',
        '    </div>',
        '    <div style="margin-bottom: 15px;">',
        '        <button id="downloadBtn" style="padding: 14px 24px; font-size: 16px; font-weight: bold; background-color: #00CC66; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">📥 Download Completed PDF</button>',
        '    </div>',
        '    <div id="canvas-container" style="position: relative; display: inline-block; width: 100%; max-width: __MAX_WIDTH__px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border: 1px solid #ccc; touch-action: manipulation;">',
        '        <img id="pdf-bg" src=\'__FIRST_PAGE_IMG__\' style="display: block; width: 100%; height: auto; pointer-events: none; user-select: none;" />',
        '        <div id="inputs-viewport" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">__ALL_INPUTS_HTML__</div>',
        '    </div>',
        '</div>',
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf-lib/1.17.1/pdf-lib.min.js"></script>',
        '<script>',
        '    window.toggleCheck = function(element) {',
        '        element.innerText = (element.innerText === "X") ? "" : "X";',
        '    };',
        '    window.adjustFontSize = function(input) {',
        '        let size = 10;',
        '        input.style.fontSize = size + "px";',
        '        while (input.scrollWidth > input.clientWidth && size > 5.5) {',
        '            size -= 0.5;',
        '            input.style.fontSize = size + "px";',
        '        }',
        '    };',
        '    const pageImages = [__IMAGES_JS_STREAM__];',
        '    let currentPage = 0;',
        '    const totalPages = __TOTAL_PAGES__;',
        '    const prevBtn = document.getElementById("prevBtn");',
        '    const nextBtn = document.getElementById("nextBtn");',
        '    const pageIndicator = document.getElementById("pageIndicator");',
        '    const bgImg = document.getElementById("pdf-bg");',
        '    const downloadBtn = document.getElementById("downloadBtn");',
        '    ',
        '    function updatePageDisplay() {',
        '        bgImg.src = pageImages[currentPage];',
        '        pageIndicator.innerText = "Page " + (currentPage + 1) + " of " + totalPages;',
        '        for(let i=0; i<totalPages; i++) {',
        '            const layer = document.getElementById("layer-" + i);',
        '            if(layer) { layer.style.display = (i === currentPage) ? "block" : "none"; }',
        '        }',
        '        prevBtn.disabled = (currentPage === 0);',
        '        nextBtn.disabled = (currentPage === totalPages - 1);',
        '        setTimeout(() => {',
        '            document.querySelectorAll(\'#canvas-container input[data-type="text"]\').forEach(el => {',
        '                if (window.adjustFontSize) window.adjustFontSize(el);',
        '            });',
        '        }, 60);',
        '    }',
        '    prevBtn.addEventListener("click", () => { if(currentPage > 0) { currentPage--; updatePageDisplay(); } });',
        '    nextBtn.addEventListener("click", () => { if(currentPage < totalPages - 1) { currentPage++; updatePageDisplay(); } });',
        '    setTimeout(() => {',
        '        document.querySelectorAll(\'#canvas-container input[data-type="text"]\').forEach(el => {',
        '            if (window.adjustFontSize) window.adjustFontSize(el);',
        '        });',
        '    }, 350);',
        '    updatePageDisplay();',
        '    downloadBtn.addEventListener("click", async function() {',
        '        try {',
        '            const pdfDataBytes = Uint8Array.from(atob("__PDF_BASE64__"), c => c.charCodeAt(0));',
        '            const pdfDoc = await PDFLib.PDFDocument.load(pdfDataBytes);',
        '            const helveticaFont = await pdfDoc.embedFont(PDFLib.StandardFonts.HelveticaBold);',
        '            const pages = pdfDoc.getPages();',
        '            const textInputs = document.querySelectorAll("#canvas-container input[data-type=\'text\']");',
        '            for (let input of textInputs) {',
        '                const pageIdx = parseInt(input.getAttribute("data-page"));',
        '                const textValue = input.value.trim();',
        '                if (textValue.length > 0) {',
        '                    const targetPage = pages[pageIdx];
