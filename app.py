# from flask import Flask, request, jsonify
# import openai
# from openai import OpenAI
# from functools import wraps
#
# app = Flask(__name__)
#
# # memory and API key storage
# api_keys = {}
# conversation_memory = {}
# initial_instructions = {
#     "role": "assistant",
#     "content": "In this conversation, you are the world's best dermatologist. Your personality is knowledgeable, vibrant, empathetic, communicative, observant, as well as communicative. Engage users in a friendly and conversational manner about their health and lifestyle (diet, exercise, sleep, stress management, etc). IMPORTANT: Keep messages as concise as possible. Make sure to cite the specific rsid (GIVE THE SPECIFIC ONE, for example rs1042602) that leads you to different diagnoses."
# }
# chatbot = None
#
# # API key validation
# def require_api_key(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         api_key = request.headers.get('X-API-Key')
#         if not api_key or api_key not in api_keys:
#             return jsonify({"error": "Valid API key required"}), 401
#         return f(*args, **kwargs)
#     return decorated_function
#
# # endpoint to set and validate API key
# @app.route('/set_api_key', methods=['POST'])
# def set_api_key():
#     data = request.json
#     api_key = data.get('api_key')
#
#     if not api_key:
#         return jsonify({"error": "No API key provided"}), 400
#
#     try:
#         client = OpenAI(api_key=api_key)
#         client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": "test"}],
#             max_tokens=5
#         )
#         api_keys[api_key] = True
#         conversation_memory[api_key] = []
#         return jsonify({"message": "API key successfully validated"}), 200
#
#     except openai.AuthenticationError:
#         return jsonify({"error": "Invalid API key"}), 401
#     except Exception as e:
#         return jsonify({"error": f"Error validating API key: {str(e)}"}), 500
#
#
# # chat endpoint with memory storage
# @app.route("/chat", methods=["POST"])
# def index():
#     if request.method == "POST":
#         try:
#             data = request.json
#             text = data.get('text', '')
#             if not text:
#                 return jsonify({"error": "No text provided"}), 400
#             api_key = request.headers.get('X-API-Key')
#
#             if api_key not in conversation_memory:
#                 conversation_memory[api_key] = []
#
#             conversation_memory[api_key].append({"role": "user", "content": text})
#
#             client = OpenAI(api_key=api_key)
#             response = client.chat.completions.create(model="gpt-4", messages=conversation_memory[api_key])
#             assistant_response = response.choices[0].message.content
#             conversation_memory[api_key].append({"role": "assistant", "content": assistant_response})
#
#             return jsonify({"message": assistant_response}), 200
#
#         except Exception as e:
#             return jsonify({"error": f"Error processing request: {str(e)}"}), 500
#
# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, render_template, request, redirect, jsonify
from functools import wraps
from openai import OpenAI


# INITIALIZING APP, CHATBOTS AND MEMORY

app = Flask(__name__)

api_keys = {}
conversation_memory = {}
initial_instructions = {
    "role": "assistant",
    "content": "In this conversation, you are the world's best dermatologist. Your personality is knowledgeable, vibrant, empathetic, communicative, observant, friendly, as well as communicative. Engage users in a friendly and conversational manner about their health and lifestyle (diet, exercise, sleep, stress management, etc). IMPORTANT: Keep messages as concise as possible. Make sure to cite the specific rsid (GIVE THE SPECIFIC ONE, for example rs1042602) that leads you to different diagnoses."
}

# API key validation
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in api_keys:
            return jsonify({"error": "Valid API key required"}), 401
        return f(*args, **kwargs)

    return decorated_function


# endpoint to set and validate API key
@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    data = request.json
    api_key = data.get('api_key')

    if not api_key:
        return jsonify({"error": "No API key provided"}), 400

    try:
        client = OpenAI(api_key=api_key)
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        api_keys[api_key] = True
        conversation_memory[api_key] = [initial_instructions]

        return jsonify({"message": "API key successfully validated"}), 200

    except Exception as e:
        return jsonify({"error": f"Error validating API key: {str(e)}"}), 500


@app.route("/chat", methods=["POST"])
def index():
    if request.method == "POST":
        try:
            data = request.json
            text = data.get('text', '')
            if not text:
                return jsonify({"error": "No text provided"}), 400
            api_key = request.headers.get('X-API-Key')

            if api_key not in conversation_memory:
                conversation_memory[api_key] = [initial_instructions]

            conversation_memory[api_key].append({"role": "user", "content": text})

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-4", messages=conversation_memory[api_key])
            assistant_response = response.choices[0].message.content
            conversation_memory[api_key].append({"role": "assistant", "content": assistant_response})

            return jsonify({"message": assistant_response}), 200

        except Exception as e:
            return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == "__main__":
    app.run("0.0.0.0")