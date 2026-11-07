
from pypdf import PdfReader

def extract_pdf_text(file_path):
    try:
        pdf = PdfReader(file_path)
        pages = []

        print("Total pages:", len(pdf.pages))

        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            print(f"Processing page {page_number}...")

            if text.strip():
                pages.append({
                    "page": page_number,
                    "text": text
                })

        return pages

    except Exception as error:
        print("Error reading PDF:", error)
        return None


if __name__ == "__main__":
    pages = extract_pdf_text("sample.pdf")

    if pages:
        print("PDF text extracted successfully!")
        print(pages[0]["text"][:100])
    else:
        print("No readable text found.")
