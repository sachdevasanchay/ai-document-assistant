
from sentence_transformers import SentenceTransformer, util
from text_chunker import split_text_into_chunks
from pdf_extractor import extract_pdf_text
from ai_service import generate_answer

# Load the AI embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks):
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        convert_to_tensor=True
    )

    return embeddings


def search_similar_chunks(question, chunks, embeddings, top_k=3, program_filter=None):
    question_embedding = model.encode(
        question,
        convert_to_tensor=True
    )

    candidate_chunks = []

    for i, chunk in enumerate(chunks):
        text = chunk["text"]

        if program_filter:
            matching_lines = []

            for line in text.splitlines():
                line = line.strip()

                if program_filter.upper() == "MCA":
                    if "MCA" in line and "MCA- Microsoft" not in line and "MBA" not in line:
                        matching_lines.append(line)

                else:
                    if program_filter.upper() in line.upper():
                        matching_lines.append(line)

            if matching_lines:
                candidate_chunks.append({
                    "page": chunk["page"],
                    "text": "\n".join(matching_lines),
                    "embedding": embeddings[i]
                })

        else:
            candidate_chunks.append({
                "page": chunk["page"],
                "text": text,
                "embedding": embeddings[i]
            })

    if not candidate_chunks:
        return []

    filtered_embeddings = model.encode(
        [chunk["text"] for chunk in candidate_chunks],
        convert_to_tensor=True
    )

    similarities = util.cos_sim(
        question_embedding,
        filtered_embeddings
    )[0]

    top_results = similarities.topk(
        k=min(top_k, len(candidate_chunks))
    )

    results = []

    for index, score in zip(top_results.indices, top_results.values):
        chunk = candidate_chunks[index.item()]

        results.append({
            "page": chunk["page"],
            "text": chunk["text"],
            "similarity": score.item()
        })

    return results



if __name__ == "__main__":
    pages = extract_pdf_text("sample.pdf")

    if pages:
        chunks = split_text_into_chunks(pages)

        print("\nCreating embeddings...")
        embeddings = create_embeddings(chunks)

        print("Embeddings created successfully!")

        question = "When is my first MCA semester exam?"

        print("\nSearching for:", question)

        results = search_similar_chunks(
            question,
            chunks,
            embeddings,
            top_k=5,
            program_filter="MCA"
        )

        for index, result in enumerate(results, start=1):
            print(f"\nResult {index}")
            print("Page:", result["page"])
            print("Similarity:", round(result["similarity"], 3))
            print("Text:", result["text"][:200])

        print("\nGenerating AI Answer...")

        answer = generate_answer(question, results)

        print("\n========== AI ANSWER ==========")
        print(answer)


        for index, result in enumerate(results, start=1):
            print(f"\nResult {index}")
            print("Page:", result["page"])
            print("Similarity:", round(result["similarity"], 3))
            print("Text:", result["text"][:200])