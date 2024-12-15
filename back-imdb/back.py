from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, PointStruct, SearchRequest
from collections import defaultdict


app = Flask(__name__)
CORS(app)

# Load BERT model and tokenizer
MODEL_NAME = "bert-base-uncased"
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
except Exception as e:
    print(f"Error loading model: {e}")
    raise

# Qdrant setup
QDRANT_ENDPOINT = "https://ad551307-1384-4c04-8808-931b23ccc62e.us-west-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "cv75oFDqAO2Iud_PfQLwCVwqXDn1JjBLhen1lTWSk318Cq9yN_dOLQ"
COLLECTION_NAME = "my_collection"
qdrant_client = QdrantClient(url=QDRANT_ENDPOINT, api_key=QDRANT_API_KEY)

# Helper function to convert text to vector
def get_text_vector(comment):
    if not comment:
        return None
    inputs = tokenizer(comment, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    vector = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return vector.tolist()

# Function to recommend films based on vector similarity
def recommend_film(comment_vector, top_k=3):
    try:
        # Search for top-n similar vectors in Qdrant
        top_n = 50  # Retrieve more points for better aggregation
        response = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=comment_vector,
            limit=top_n
        )
        
        # Aggregate scores by Film ID
        film_scores = defaultdict(list)
        for hit in response:
            film_id = hit.payload["Film ID"]
            score = hit.score
            film_scores[film_id].append(score)
        
        # Calculate aggregate similarity scores (e.g., average)
        aggregate_scores = {
            film_id: sum(scores) / len(scores)  # Use average score
            for film_id, scores in film_scores.items()
        }
        
        # Sort films by aggregate similarity score
        sorted_films = sorted(aggregate_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top-k films
        return [film_id for film_id, _ in sorted_films[:top_k]]
    
    except Exception as e:
        print(f"Error during recommendation: {e}")
        return []

@app.route('/analyze', methods=['POST'])
def analyze_comment():
    try:
        data = request.get_json()
        comment = data.get('comment')

        if not comment:
            return jsonify({"error": "Comment is required"}), 400

        # Convert comment to vector
        comment_vector = get_text_vector(comment)
        if not comment_vector:
            return jsonify({"error": "Failed to vectorize the comment"}), 500

        # Recommend films using Qdrant
        recommendations = recommend_film(comment_vector)

        # External sentiment analysis (optional)
        payload = {
            "model": "mistral:latest",
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert film sentiment and genre analyzer. \
                    Analyze the provided film comment and return a STRICTLY FORMATTED JSON response with sentiment, sentiment_score, genres, emotions, and confidence."""
                },
                {
                    "role": "user",
                    "content": f"Analyze the following film comment: '{comment}'"
                }
            ],
            "stream": False
        }

        response = requests.post(
            "https://irisi_3-hiiigd-11434.svc-usw2.nicegpu.com/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=False
        )

        if response.status_code == 200:
            sentiment_analysis = response.json()
            return jsonify({
                "recommendations": recommendations,
                "sentiment_analysis": sentiment_analysis
            })
        else:
            return jsonify({
                "recommendations": recommendations,
                "sentiment_analysis": "Failed to fetch sentiment analysis"
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
