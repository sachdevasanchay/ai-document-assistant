
import os
from google import genai
from dotenv import load_dotenv
import streamlit as st

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
Page: {result['page']}
Information: {result['text']}
"""

    prompt = f"""
You are a helpful PDF document assistant.

Answer the question using ONLY the provided document context.

If the answer is unavailable, clearly say so.
Never invent dates or information.
Mention the source page number.

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}
"""

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt
    )

    return response.text
