
import os
from datetime import datetime, timezone

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in .env file")


# MongoDB connection
client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000
)

db = client["ai_document_assistant"]

documents_collection = db["documents"]
conversations_collection = db["conversations"]


# Create unique conversation index
conversations_collection.create_index(
    [("document_name", 1), ("name", 1)],
    unique=True
)


def test_connection():

    try:
        client.admin.command("ping")
        print("MongoDB connected successfully!")
        return True

    except Exception as error:
        print("MongoDB connection failed:", error)
        return False


# Save document information and extracted chunks
def save_document(file_name, chunks):

    document = {
        "_id": file_name,
        "file_name": file_name,
        "chunks": chunks,
        "created_at": datetime.now(timezone.utc)
    }

    documents_collection.update_one(
        {"_id": file_name},
        {"$set": document},
        upsert=True
    )


# Get all saved documents
def get_documents():

    return list(documents_collection.find())


# Get a particular document
def get_document(file_name):

    return documents_collection.find_one({
        "_id": file_name
    })


# Delete a document and its conversations
def delete_document(file_name):

    documents_collection.delete_one({
        "_id": file_name
    })

    conversations_collection.delete_many({
        "document_name": file_name
    })


# Save or update a conversation
def save_conversation(document_name, conversation_name, messages):

    conversation = {
        "document_name": document_name,
        "name": conversation_name,
        "messages": messages,
        "updated_at": datetime.now(timezone.utc)
    }

    conversations_collection.update_one(
        {
            "document_name": document_name,
            "name": conversation_name
        },
        {"$set": conversation},
        upsert=True
    )


# Get all conversations for a document
def get_conversations(document_name):

    conversations = conversations_collection.find({
        "document_name": document_name
    })

    result = {}

    for conversation in conversations:

        result[conversation["name"]] = {
            "messages": conversation.get("messages", [])
        }

    return result


# Rename a conversation
def rename_conversation(document_name, old_name, new_name):

    return conversations_collection.update_one(
        {
            "document_name": document_name,
            "name": old_name
        },
        {
            "$set": {
                "name": new_name,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )


# Delete a conversation
def delete_conversation(document_name, conversation_name):

    conversations_collection.delete_one({
        "document_name": document_name,
        "name": conversation_name
    })


if __name__ == "__main__":

    test_connection()
