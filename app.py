from flask import Flask, request, jsonify
import openai
from openai import OpenAI

client = OpenAI(api_key=api_key,
api_key=api_key)
import os
from functools import wraps

app = Flask(__name__)

# Dictionary to store active API keys
api_keys = {}

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in api_keys:
            return jsonify({"error": "Valid API key required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    data = request.json
    api_key = data.get('api_key')

    if not api_key:
        return jsonify({"error": "No API key provided"}), 400

    try:
        # Test the API key with a simple completion
        client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=5)

        # If no error is raised, store the API key
        api_keys[api_key] = True
        return jsonify({"message": "API key successfully validated"}), 200

    except openai.AuthenticationError:
        return jsonify({"error": "Invalid API key"}), 401
    except Exception as e:
        return jsonify({"error": f"Error validating API key: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
@require_api_key
def chat():
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "No text provided"}), 400

        # Use the API key from the request header
        api_key = request.headers.get('X-API-Key')

        # Call OpenAI API
        response = client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text}
        ])

        # Extract the assistant's response
        assistant_response = response.choices[0].message.content

        return jsonify({
            "message": assistant_response,
            "tokens_used": response.usage.total_tokens
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)