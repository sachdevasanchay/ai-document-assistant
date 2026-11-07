document_name = "company_policy.pdf"
total_pages = 25
is_uploaded = True

print(document_name)
print(total_pages)
print(is_uploaded)

documents = [
    "company_policy.pdf",
    "employee_handbook.pdf",
    "project_report.pdf"
]

print(documents)

for document in documents:
    print(document)

document = {
    "name": "company_policy.pdf",
    "pages": 25,
    "uploaded": True
}

print(document["name"])
print(document["pages"])

def welcome_user(name):
    print("Welcome", name)


welcome_user("Sanchay")

def count_characters(text):

    return len(text)


result = count_characters("Hello Python")

print(result)

total_pages = 0

if total_pages > 0:
    print("PDF contains pages")
else:
    print("PDF is empty")