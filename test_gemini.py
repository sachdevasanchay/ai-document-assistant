from ai_service import generate_answer

question = "When is the first MCA exam?"

search_results = [
    {
        "page": 5,
        "text": "MCA ONCA301 Advanced Database Management System 02-Jan-27 10:00 AM - 1:00 PM"
    }
]

answer = generate_answer(question, search_results)

print("\nGemini Answer:")
print(answer)