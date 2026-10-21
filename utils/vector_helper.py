import os
from dotenv import load_dotenv

# Load environment variables immediately
load_dotenv()

from pinecone import Pinecone
from openai import OpenAI

def get_pinecone_index():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY is missing from environment variables or .env file.")
    pc = Pinecone(api_key=api_key)
    return pc.Index("expense-audit-index")  # <-- Updated to your exact index name

def upsert_transactions_to_pinecone(transactions_list):
    try:
        api_key = os.getenv("PINECONE_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") # Fallback support
        if not api_key:
            return False
            
        pc = Pinecone(api_key=api_key)
        index = pc.Index("expense-audit-index")  # <-- Updated here too
        
        # If using OpenAI for embeddings (text-embedding-3-small):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        vectors = []
        for i, tx in enumerate(transactions_list):
            text_to_embed = f"Date: {tx.get('Date')}, Segment: {tx.get('Segment')}, Merchant: {tx.get('Merchant_Source')}, Amount: {tx.get('Amount')}, Channel: {tx.get('Channel')}"
            
            response = client.embeddings.create(
                input=[text_to_embed],
                model="text-embedding-3-small"
            )
            vector_values = response.data[0].embedding
            vector_id = f"tx_{tx.get('Date')}_{i}_{abs(hash(text_to_embed)) % 100000}"
            
            vectors.append({
                "id": vector_id,
                "values": vector_values,
                "metadata": {
                    "date": str(tx.get('Date')),
                    "segment": str(tx.get('Segment')),
                    "merchant": str(tx.get('Merchant_Source')),
                    "amount": float(tx.get('Amount')),
                    "channel": str(tx.get('Channel')),
                    "text": text_to_embed
                }
            })
            
        if vectors:
            index.upsert(vectors=vectors)
        return True
    except Exception as e:
        print(f"Pinecone vector upsert error: {e}")
        return False

def query_pinecone_transactions(user_query, top_k=5):
    try:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            return []
            
        pc = Pinecone(api_key=api_key)
        index = pc.Index("expense-audit-index")  # <-- Updated here too
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.embeddings.create(
            input=[user_query],
            model="text-embedding-3-small"
        )
        query_vector = response.data[0].embedding
        
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )
        
        return [match['metadata'] for match in results.get('matches', [])]
    except Exception as e:
        print(f"Pinecone query error: {e}")
        return []