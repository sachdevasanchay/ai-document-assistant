
from pypdf import PdfReader
import fitz
import pytesseract
from PIL import Image
from io import BytesIO


import shutil
import pytesseract

tesseract_path = shutil.which("tesseract")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

def extract_pdf_text(file_path):
    try:
        pdf = PdfReader(file_path)

        if hasattr(file_path, "getvalue"):
            pdf_document = fitz.open(
                stream=file_path.getvalue(),
                filetype="pdf"
            )
        else:
            pdf_document = fitz.open(file_path)

        pages = []

        print("Total pages:", len(pdf.pages))

        for page_number, page in enumerate(pdf.pages, start=1):

            print(f"Processing page {page_number}...")

            text = page.extract_text() or ""

            # Get image blocks from the PDF page
            pdf_page = pdf_document[page_number - 1]

            image_blocks = [
                block
                for block in pdf_page.get_text("dict")["blocks"]
                if block["type"] == 1
            ]

            ocr_text = []

            # Use OCR when scanned images are present
            if image_blocks:

                print(f"Found {len(image_blocks)} image(s) on page {page_number}.")

                for image_block in image_blocks:

                    bbox = fitz.Rect(image_block["bbox"])

                    pix = pdf_page.get_pixmap(
                        matrix=fitz.Matrix(2, 2),
                        clip=bbox
                    )

                    image = Image.open(
                        BytesIO(pix.tobytes("png"))
                    )

                    extracted_text = pytesseract.image_to_string(image)

                    if extracted_text.strip():
                        ocr_text.append(extracted_text)

            # Fallback for pages without selectable text or image blocks
            elif not text.strip():

                print(f"Using full-page OCR for page {page_number}...")

                pix = pdf_page.get_pixmap(
                    matrix=fitz.Matrix(2, 2)
                )

                image = Image.open(
                    BytesIO(pix.tobytes("png"))
                )

                extracted_text = pytesseract.image_to_string(image)

                if extracted_text.strip():
                    ocr_text.append(extracted_text)

            # Combine selectable text and OCR text
            final_text = text

            if ocr_text:
                final_text += "\n\n" + "\n\n".join(ocr_text)

            if final_text.strip():
                pages.append({
                    "page": page_number,
                    "text": final_text
                })

        pdf_document.close()

        return pages

    except Exception as error:
        print("Error reading PDF:", error)
        return None


if __name__ == "__main__":

    pages = extract_pdf_text("sample.pdf")

    if pages:
        print("PDF text extracted successfully!")
        print(pages[0]["text"][:1000])
    else:
        print("No readable text found.")
