
from sentence_transformers import SentenceTransformer, util
from text_chunker import split_text_into_chunks
from pdf_extractor import extract_pdf_text
from ai_service import generate_answer
import re
import math


# Load the AI embedding model only when required
model = None


def get_embedding_model():
    global model

    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    return model


def create_embeddings(chunks):
    embedding_model = get_embedding_model()

    texts = [chunk["text"] for chunk in chunks]

    embeddings = embedding_model.encode(
        texts,
        convert_to_tensor=True
    )

    return embeddings


def get_keywords(text):
    stop_words = {
        "the", "is", "are", "was", "were", "when",
        "what", "where", "who", "how", "why",
        "a", "an", "and", "or", "in", "on", "at",
        "to", "for", "of", "my", "me", "your",
        "this", "that", "it", "do", "does", "did"
    }

    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    return set(
        word for word in words
        if word not in stop_words
    )


def calculate_keyword_scores(question, candidate_chunks):

    query_keywords = get_keywords(question)

    if not query_keywords:
        return [0.0] * len(candidate_chunks)

    document_keywords = [
        get_keywords(chunk["text"])
        for chunk in candidate_chunks
    ]

    total_documents = len(document_keywords)

    # Calculate how important each query keyword is
    keyword_weights = {}

    for keyword in query_keywords:

        document_frequency = sum(
            1 for words in document_keywords
            if keyword in words
        )

        keyword_weights[keyword] = (
            math.log(
                (total_documents + 1) /
                (document_frequency + 1)
            ) + 1
        )

    total_weight = sum(keyword_weights.values())

    keyword_scores = []

    for words in document_keywords:

        matched_weight = sum(
            keyword_weights[keyword]
            for keyword in query_keywords
            if keyword in words
        )

        score = matched_weight / total_weight

        keyword_scores.append(score)

    return keyword_scores


def search_similar_chunks(
    question,
    chunks,
    embeddings,
    top_k=3,
    program_filter=None,
    min_similarity=0.25
):

    embedding_model = get_embedding_model()

    question_embedding = embedding_model.encode(
        question,
        convert_to_tensor=True
    )

    candidate_chunks = []
    candidate_indices = []

    for i, chunk in enumerate(chunks):

        text = chunk["text"]

        if program_filter:

            matching_lines = []

            for line in text.splitlines():

                if program_filter.lower() in line.lower():
                    matching_lines.append(line)

            if matching_lines:

                candidate_chunks.append({
                    "page": chunk["page"],
                    "text": "\n".join(matching_lines)
                })

                candidate_indices.append(i)

        else:

            candidate_chunks.append({
                "page": chunk["page"],
                "text": text
            })

            candidate_indices.append(i)

    if not candidate_chunks:
        return []

    # Get embeddings for candidate chunks
    if program_filter:

        filtered_embeddings = embedding_model.encode(
            [chunk["text"] for chunk in candidate_chunks],
            convert_to_tensor=True
        )

    else:

        filtered_embeddings = embeddings[candidate_indices]

    # Semantic search
    semantic_scores = util.cos_sim(
        question_embedding,
        filtered_embeddings
    )[0]

    # Keyword search
    keyword_scores = calculate_keyword_scores(
        question,
        candidate_chunks
    )

    results = []

    for i, chunk in enumerate(candidate_chunks):

        semantic_score = semantic_scores[i].item()
        keyword_score = keyword_scores[i]

        # Combine semantic and keyword scores
        hybrid_score = (
            0.65 * semantic_score +
            0.35 * keyword_score
        )

        if hybrid_score < min_similarity:
            continue

        results.append({
            "page": chunk["page"],
            "text": chunk["text"],
            "similarity": hybrid_score,
            "semantic_score": semantic_score,
            "keyword_score": keyword_score
        })

    # Sort by highest hybrid score
    results.sort(
        key=lambda result: result["similarity"],
        reverse=True
    )

    return results[:top_k]


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
            program_filter=None,
            min_similarity=0.25
        )

        if results:

            for index, result in enumerate(results, start=1):

                print(f"\nResult {index}")
                print("Page:", result["page"])
                print("Hybrid Score:", round(result["similarity"], 3))
                print("Semantic Score:", round(result["semantic_score"], 3))
                print("Keyword Score:", round(result["keyword_score"], 3))
                print("Text:", result["text"][:200])

            print("\nGenerating AI Answer...")

            answer = generate_answer(question, results)

            print("\n========== AI ANSWER ==========")
            print(answer)

        else:

            print("No relevant information found in the document.")
