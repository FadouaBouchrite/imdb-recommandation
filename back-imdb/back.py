from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import torch
from transformers import AutoTokenizer, AutoModel

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# API endpoint and headers for external API
API_URL = "https://irisi_3-hiiigd-11434.svc-usw2.nicegpu.com/api/chat"
HEADERS = {"Content-Type": "application/json"}
def get_text_vector(comment):
    """
    Converts a comment into a numerical vector representation using a pre-trained BERT model.
    """
    if not comment:  # Check if the text is empty
        return None

    # Tokenize the input text
    inputs = tokenizer(comment, return_tensors="pt", truncation=True, padding=True, max_length=512)

    # Generate embeddings using the BERT model
    with torch.no_grad():
        outputs = model(**inputs)

    # Compute the mean of the embeddings for a single vector representation
    vector = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
    print(vector)
    return vector.tolist()  # Return the full vector as a list
# Load BERT model and tokenizer
MODEL_NAME = "bert-base-uncased"  # You can adjust this to any compatible model
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
except Exception as e:
    print(f"Error loading model: {e}")
    raise

@app.route('/analyze', methods=['POST'])
def analyze_comment():
    try:
        # Get the comment from the request
        data = request.get_json()
        comment = data.get('comment')
        
        get_text_vector(comment)

        if not comment:
            return jsonify({"error": "Comment is required"}), 400

        # Payload to send to the external API
        payload = {
            "model": "mistral:latest",
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert film sentiment and genre analyzer. 
Analyze the provided film comment and return a STRICTLY FORMATTED JSON response with the following keys:
- sentiment: A string value of either \"positive\", \"negative\", or \"neutral\"
- sentiment_score: A float between -1.0 (most negative) and 1.0 (most positive)
- detected_genres: An array of film genres (max 3) that best match the comment's context
- key_emotions: An array of emotions detected in the comment (max 3)
- confidence: A float between 0.0 and 1.0 representing the confidence of the analysis
Ensure the JSON is valid and parseable. If any field cannot be determined, use a sensible default value.

Example output format:
{
    \"sentiment\": \"positive\",
    \"sentiment_score\": 0.75,
    \"detected_genres\": [\"Comedy\", \"Drama\"],
    \"key_emotions\": [\"Excitement\", \"Joy\"],
    \"confidence\": 0.92
}"""
                },
                {
                    "role": "user",
                    "content": f"Analyze the following film comment: '{comment}'"
                }
            ],
            "stream": False
        }

        # Make the request to the external API
        response = requests.post(API_URL, json=payload, headers=HEADERS, verify=False)

        # Handle API response
        if response.status_code == 200:
            result = response.json()
            try:
                sentiment_analysis = json.loads(result.get("message", {}).get("content", "{}"))
                return jsonify(sentiment_analysis)
            except json.JSONDecodeError:
                return jsonify({
                    "error": "Failed to parse sentiment analysis",
                    "raw_response": result.get("message", {}).get("content", "No response")
                }), 500
        else:
            return jsonify({"error": "Failed to process the comment", "details": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
