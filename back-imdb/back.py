from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, PointStruct, SearchRequest
from collections import defaultdict

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Constants
MODEL_NAME = "bert-base-uncased"
QDRANT_ENDPOINT = "https://ad551307-1384-4c04-8808-931b23ccc62e.us-west-1-0.aws.cloud.qdrant.io"
QDRANT_API_KEY = "cv75oFDqAO2Iud_PfQLwCVwqXDn1JjBLhen1lTWSk318Cq9yN_dOLQ"
COLLECTION_NAME = "my_collection"
SENTIMENT_API_URL = "https://irisi_3-hiiigd-11434.svc-usw2.nicegpu.com/api/chat"

# Global Variables
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
except Exception as e:
    raise RuntimeError(f"Error loading BERT model: {e}")

qdrant_client = QdrantClient(url=QDRANT_ENDPOINT, api_key=QDRANT_API_KEY)

# Utility Functions

def get_text_vector(comment):
    """
    Convert a comment to a vector representation using the BERT model.
    
    Args:
        comment (str): The comment text to be converted.
    
    Returns:
        list: The vector representation of the comment.
    
    Raises:
        ValueError: If the provided comment is empty.
    """
    if not comment:
        raise ValueError("Comment cannot be empty")
    inputs = tokenizer(comment, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    vector = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    return vector.tolist()

def recommend_film(comment_vector, sentiment, top_k=3, top_n=50):
    """
    Recommend films based on the vector similarity in Qdrant and sentiment analysis.
    
    Args:
        comment_vector (list): The vector representation of the comment.
        sentiment (str): The sentiment of the comment ("positive" or "negative").
        top_k (int): The number of top films to return.
        top_n (int): The number of films to retrieve from Qdrant.
    
    Returns:
        list: A list of recommended film IDs.
    
    Raises:
        RuntimeError: If an error occurs while retrieving recommendations from Qdrant.
    """
    try:
        response = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=comment_vector,
            limit=top_n
        )

        film_scores = defaultdict(list)
        for hit in response:
            film_id = hit.payload["Film ID"]
            score = hit.score
            film_scores[film_id].append(score)

        aggregate_scores = {
            film_id: sum(scores) / len(scores)
            for film_id, scores in film_scores.items()
        }

        if sentiment == "positive":
            sorted_films = sorted(aggregate_scores.items(), key=lambda x: x[1], reverse=True)
        else:  # For negative sentiment, sort by the farthest distance
            sorted_films = sorted(aggregate_scores.items(), key=lambda x: x[1])

        return [film_id for film_id, _ in sorted_films[:top_k]]

    except Exception as e:
        raise RuntimeError(f"Error during film recommendation: {e}")

def fetch_sentiment_analysis(comment):
    """
    Fetch sentiment analysis for a given comment using an external sentiment API.
    
    Args:
        comment (str): The film comment to be analyzed.
    
    Returns:
        dict: The sentiment analysis result in JSON format.
    
    Raises:
        RuntimeError: If the sentiment API request fails.
    """
    payload = {
        "model": "mistral:latest",
        "messages": [
            {
                "role": "system",
                "content": """You are an expert film sentiment and genre analyzer. Analyze the provided film comment and return a STRICTLY FORMATTED JSON response with sentiment, sentiment_score, genres, emotions, and confidence."""
            },
            {
                "role": "user",
                "content": f"Analyze the following film comment: '{comment}'"
            }
        ],
        "stream": False
    }

    response = requests.post(
        SENTIMENT_API_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        verify=False
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"Failed to fetch sentiment analysis: {response.status_code} - {response.text}")

def validate_recommendations(comment, recommendations):
    """
    Validate whether the recommended films align with the sentiment and intent of the user's comment.
    
    Args:
        comment (str): The user's comment about the film.
        recommendations (list): The list of recommended films to validate.
    
    Returns:
        dict: The validation result in JSON format.
    
    Raises:
        RuntimeError: If the validation request fails.
    """
    payload = {
        "model": "mistral:latest",
        "messages": [
            {
                "role": "system",
                "content": """You are an expert recommendation validator. Check if the following recommended films match the intent and sentiment of the user's comment. Return a STRICTLY FORMATTED JSON response with validation and confidence."""
            },
            {
                "role": "user",
                "content": f"Comment: '{comment}', Recommendations: {recommendations}"
            }
        ],
        "stream": False
    }

    response = requests.post(
        SENTIMENT_API_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        verify=False
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"Failed to validate recommendations: {response.status_code} - {response.text}")

# Routes

@app.route('/analyze', methods=['POST'])
def analyze_comment():
    """
    Analyze a film comment to provide sentiment analysis, recommendations, and validation.

    This route performs the following tasks:
    1. Accepts a film comment.
    2. Converts the comment to a vector representation.
    3. Fetches sentiment analysis for the comment.
    4. Recommends films based on the sentiment and comment vector.
    5. Validates the recommendations against the user's comment.

    Returns:
        dict: A JSON object containing recommendations, sentiment analysis, and validation result.
    
    Raises:
        400: If the comment is missing in the request.
        500: If any error occurs during the process.
    """
    try:
        data = request.get_json()
        comment = data.get('comment')

        if not comment:
            return jsonify({"error": "Comment is required"}), 400

        # Convert comment to vector
        comment_vector = get_text_vector(comment)

        # Sentiment analysis
        sentiment_analysis = fetch_sentiment_analysis(comment)
        sentiment = sentiment_analysis.get("sentiment", "positive")

        # Recommend films
        recommendations = recommend_film(comment_vector, sentiment, top_k=6)

        # Limit recommendations to top 3 for output
        top_recommendations = recommendations[:3]

        # Validate recommendations
        validation = validate_recommendations(comment, top_recommendations)

        return jsonify({
            "recommendations": top_recommendations,
            "sentiment_analysis": sentiment_analysis,
            "recommendation_validation": validation
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
