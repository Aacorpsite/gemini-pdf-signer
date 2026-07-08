        # --- FIXED MOBILE LAYOUT: PREVIEW FIRST, FIELDS SECOND ---
        # Show the live PDF preview at the top so it's easily visible on phone screens
        st.subheader("👁️ Document Preview")
        output_doc = fitz.open(stream=st.session_state.pdf_data, filetype="pdf")
        
        # Overlay the signature if saved
        if st.session_state.signature_saved and st.session_state.signature_saved["page"] == page_num:
            sig = st.session_state.signature_saved
            p = output_doc[sig["page"]]
            scale_x, scale_y = p.rect.width / pix.width, p.rect.height / pix.height
            
            sig_img = Image.fromarray(sig["image"].astype('uint8'), 'RGBA')
            img_byte_arr = io.BytesIO()
            sig_img.save(img_byte_arr, format='PNG')
            
            rect = fitz.Rect(sig["x"] * scale_x, sig["y"] * scale_y, (sig["x"] + 120) * scale_x, (sig["y"] + 60) * scale_y)
            p.insert_image(rect, stream=img_byte_arr.getvalue())

        # Render the PDF image right here
        st.image(output_doc[page_num].get_pixmap(dpi=150).tobytes("png"), use_container_width=True)
        
        st.download_button(
            label="📥 Download Finished PDF",
            data=output_doc.write(),
            file_name="completed_and_signed.pdf",
            mime="application/pdf"
        )
        st.write("---")

        # Now display the fillable input fields and signature pad underneath the preview
        widgets = list(page.widgets())
        if widgets:
            st.subheader("🖋️ Fill Form Fields")
            for widget in widgets:
                new_val = st.text_input(f"Line: '{widget.field_name}'", value=widget.field_value, key=f"fld_{widget.xref}")
                if new_val != widget.field_value:
                    widget.field_value = new_val
                    widget.update()
            
            st.session_state.pdf_data = doc.write()
            st.write("---")

        # Digital Signature Pad
        st.subheader("🖊️ Draw Your Signature")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=3,
            stroke_color="#0000FF",
            background_color="#f0f2f6",
            height=120,
            width=300,
            drawing_mode="freedraw",
            key="signature_pad"
        )
        
        col_x, col_y = st.columns(2)
        with col_x:
            sig_x = st.number_input("Move Signature X (Left/Right)", value=50, step=10)
        with col_y:
            sig_y = st.number_input("Move Signature Y (Up/Down)", value=150, step=10)

        if st.button("💾 Apply Signature to Document"):
            if canvas_result.image_data is not None:
                st.session_state.signature_saved = {
                    "page": page_num,
                    "image": canvas_result.image_data,
                    "x": sig_x,
                    "y": sig_y
                }
                st.success("Signature locked in place!")
                st.rerun()
