
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


def generate_answer(question, search_results):

    if not search_results:
        return "I could not find relevant information in the PDF."

    context = ""

    for result in search_results:
        context += f"""
[Page {result['page']}]
{result['text']}
"""

    prompt = f"""
You are a helpful AI document assistant.

Your task is to answer the user's question using ONLY the
provided document context.

Follow these rules strictly:

1. Use only information available in the document context.
2. Do not use your general knowledge to fill missing information.
3. Do not invent dates, names, numbers, facts, or explanations.
4. If the answer cannot be found in the provided context,
   respond with:
   "I could not find this information in the provided PDF context."
5. Mention the relevant page number in your answer using
   this format: [Page 3].
6. If information comes from multiple pages, cite all relevant pages.
7. Keep the answer clear, accurate, and easy to understand.
8. Do not cite a page unless the provided context contains
   information supporting your answer.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER:
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=prompt
    )

    if not response or not response.text:
        return "I couldn't generate an answer. Please try again."

    return response.text.strip()
