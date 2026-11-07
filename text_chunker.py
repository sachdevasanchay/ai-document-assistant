
from pdf_extractor import extract_pdf_text

def split_text_into_chunks(pages, chunk_size=500, overlap=100):
    chunks = []

    for page in pages:
        text = page["text"]

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk = text[start:end]

            if chunk.strip():
                chunks.append({
                    "page": page["page"],
                    "text": chunk
                })

            if end >= len(text):
                break

            start = end - overlap

    return chunks


if __name__ == "__main__":
    pages = extract_pdf_text("sample.pdf")

    if pages:
        chunks = split_text_into_chunks(pages)

        print("\nTotal chunks created:", len(chunks))

        for index, chunk in enumerate(chunks, start=1):
            print(f"\nChunk {index}")
            print("Page:", chunk["page"])
            print("Text:", chunk["text"][:150])
