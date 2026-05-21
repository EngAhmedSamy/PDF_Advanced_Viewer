# app.py

import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfMerger
import tempfile
import os

st.set_page_config(layout="wide")

st.title("📄 PDF Separator Tool")

# -----------------------------
# Session State
# -----------------------------
if "pages" not in st.session_state:
    st.session_state.pages = []

# -----------------------------
# Functions
# -----------------------------

def pdf_to_images(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))

        img = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        pages.append({
            "type": "original",
            "image": img,
            "label": f"Page {page_num + 1}"
        })

    return pages


def create_red_separator(title="SECTION"):
    width, height = A4
    img = Image.new("RGB", (int(width), int(height)), color=(200, 0, 0))

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()

    text = title.upper()

    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (img.width - text_width) / 2
    y = (img.height - text_height) / 2

    draw.text((x, y), text, fill="white", font=font)

    return img


def export_pdf(pages):
    temp_files = []

    merger = PdfMerger()

    for i, page in enumerate(pages):
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        image = page["image"]

        image_rgb = image.convert("RGB")

        pdf_bytes = io.BytesIO()
        image_rgb.save(pdf_bytes, format="PDF")
        pdf_bytes.seek(0)

        temp_pdf.write(pdf_bytes.read())
        temp_pdf.close()

        temp_files.append(temp_pdf.name)

        merger.append(temp_pdf.name)

    output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name

    merger.write(output_path)
    merger.close()

    for f in temp_files:
        os.remove(f)

    return output_path


# -----------------------------
# Upload PDF
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Scanned PDF",
    type=["pdf"]
)

if uploaded_file:

    if not st.session_state.pages:
        st.session_state.pages = pdf_to_images(uploaded_file)

    st.subheader("PDF Pages")

    # -----------------------------
    # Display Pages
    # -----------------------------

    for idx, page in enumerate(st.session_state.pages):

        st.markdown("---")

        col1, col2 = st.columns([5, 1])

        with col1:
            st.image(
                page["image"],
                caption=page["label"],
                use_container_width=True
            )

        with col2:

            st.write("")

            # Delete Button
            if st.button(
                "🗑 Delete",
                key=f"delete_{idx}"
            ):
                st.session_state.pages.pop(idx)
                st.rerun()

            # Move Up
            if idx > 0:
                if st.button(
                    "⬆ Up",
                    key=f"up_{idx}"
                ):
                    st.session_state.pages[idx], st.session_state.pages[idx - 1] = (
                        st.session_state.pages[idx - 1],
                        st.session_state.pages[idx]
                    )
                    st.rerun()

            # Move Down
            if idx < len(st.session_state.pages) - 1:
                if st.button(
                    "⬇ Down",
                    key=f"down_{idx}"
                ):
                    st.session_state.pages[idx], st.session_state.pages[idx + 1] = (
                        st.session_state.pages[idx + 1],
                        st.session_state.pages[idx]
                    )
                    st.rerun()

        # -----------------------------
        # Insert Separator
        # -----------------------------
        if idx < len(st.session_state.pages) - 1:
                        
            st.markdown("### ➕ Add Separator")
            
            col_sep1, col_sep2 = st.columns([3, 1])
            
            with col_sep1:
                separator_text = st.text_input(
                    "Separator Title",
                    value="SECTION",
                    key=f"separator_text_{idx}"
                )
            
            with col_sep2:
                st.write("")
                st.write("")
            
                if st.button(
                    "Insert",
                    key=f"insert_separator_{idx}"
                ):
            
                    separator_img = create_red_separator(separator_text)
            
                    separator_page = {
                        "type": "separator",
                        "image": separator_img,
                        "label": separator_text
                    }
            
                    st.session_state.pages.insert(
                        idx + 1,
                        separator_page
                    )
            
                    st.rerun()
    
    # -----------------------------
    # Export
    # -----------------------------
    st.markdown("---")

    if st.button("📥 Export Final PDF"):

        output_pdf = export_pdf(st.session_state.pages)

        with open(output_pdf, "rb") as f:
            st.download_button(
                label="Download PDF",
                data=f,
                file_name="final_document.pdf",
                mime="application/pdf"
            )
