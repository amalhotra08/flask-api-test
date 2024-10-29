from flask import Flask, request, jsonify
import openai
from openai import OpenAI
from functools import wraps

app = Flask(__name__)

# memory and API key storage
api_keys = {}
conversation_memory = {}
initial_instructions = {
    "role": "assistant",
    "content": "In this conversation, you are the world's best dermatologist. Your personality is knowledgeable, vibrant, empathetic, communicative, observant, as well as communicative. Engage users in a friendly and conversational manner about their health and lifestyle (diet, exercise, sleep, stress management, etc). IMPORTANT: Keep messages as concise as possible. Make sure to cite the specific rsid (GIVE THE SPECIFIC ONE, for example rs1042602) that leads you to different diagnoses."
}
chatbot = None

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
        conversation_memory[api_key] = []
        return jsonify({"message": "API key successfully validated"}), 200

    except openai.AuthenticationError:
        return jsonify({"error": "Invalid API key"}), 401
    except Exception as e:
        return jsonify({"error": f"Error validating API key: {str(e)}"}), 500


# chat endpoint with memory storage
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
                conversation_memory[api_key] = []

            conversation_memory[api_key].append({"role": "user", "content": text})

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-4", messages=conversation_memory[api_key])
            assistant_response = response.choices[0].message.content
            conversation_memory[api_key].append({"role": "assistant", "content": assistant_response})

            return jsonify({"message": assistant_response}), 200

        except Exception as e:
            return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)





from flask import Flask, render_template, request, redirect, jsonify
import os
import time
import ast
import sqlite3
import pandas as pd

from langchain import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from chatbots import Chatbots, parse_output
from compare_rsids import compare_gene_conditions

app = Flask(__name__)

params = {'open_api_key': os.environ['api_key']}
chatbot = Chatbots(params)

memory_loaded = False

# initial prompt
chatbot.conversation_chain.predict( input=
  f"In this conversation, you are the world's best dermatologist. Your personality is knowledgeable, vibrant, empathetic, communicative, observant, as well as communicative. Engage users in a friendly and conversational manner about their health and lifestyle (diet, exercise, sleep, stress management, etc). IMPORTANT: Keep messages as concise as possible. Make sure to cite the specific rsid (GIVE THE SPECIFIC ONE, for example Rs1042602) that leads you to different diagnoses."
)

reply = parse_output(chatbot.chat_bot_memory.load_memory_variables({})['history'])

username = " "

# connect with the front-end
@app.route("/username-endpoint", methods=["POST"])
def username_endpoint():
    input = request.get_json()
    username = input["username"]

    global memory_loaded
    if not memory_loaded:
        chatbot.database_file_name = username + "_records.txt"
        chatbot.reading_history(chatbot.database_file_name)
        chatbot.initialize_chains()
        chatbot.memory_loaded = True
        memory_loaded = True
        return redirect("/")
    else:
        return jsonify({"message": "username already loaded."})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user_input"]
        chat_response = chatbot.get_response(user_input)
        print(chat_response)
        response = chat_response['response']
        emotion_image_url = chat_response["emotion_img_url"]
        print(response, emotion_image_url)
        # TEXT TO SPEECH
        chatbot.text_to_speech(response)

        data = {
            "messages": chatbot.messages,
            "emotion_image": emotion_image_url,  # Update to use the new image URL
            "summary": chatbot.current_summary
        }
        return render_template("index.html", data=data, response=response)
    else:
        default_messages = [{
            "role": "assistant",
            "content": "Hello! How can I assist you today?",
            "time": time.ctime(time.time()),
            "emotion_image": chatbot.emotion_avatars["neutral"]
        }]
        data = {
            "messages":
                chatbot.messages if len(chatbot.messages) > 0 else default_messages,
            "emotion_image":
                chatbot.messages[-1]["emotion_image"] if len(chatbot.messages) > 0 else
                default_messages[-1]["emotion_image"],
            "summary":
                chatbot.current_summary
        }
        return render_template("index.html", data=data)


@app.route('/genomic_data', methods=['POST'])
def upload_genomic_data():
    if 'genomicFile' not in request.files:
        return 'No file part'

    file = request.files['genomicFile']

    if file.filename == '':
        return 'No selected file'
    else:
        print(type(file))

    # Here, you can save the file or process it as needed
    # For example, save it to a folder on the server

    file.save("uploads/" + file.filename)

    compare_gene_conditions('uploads/' + file.filename, 'gene_conditions.csv')
    print("gene_conditions.csv was successfully generated.")
    # BETA
    conditions_input = ""
    res = pd.read_csv('gene_conditions.csv')
    print('BRUH')
    for index, row in res.iterrows():
        conditions_input += f'{row["ID"]} causes {row["Summary"]}. '
    # BETA
    # TODO: ADD THE STRING OF "[condition] due to [rsid]" string here
    print(conditions_input)
    chatbot.conversation_chain.predict(
        input=
        f"My conditions due to my genomic data are as follows: {conditions_input}"
    )

    return 'File uploaded and analyzed successfully'

  
@app.route('/process_genomic_data', methods=['POST'])
def process_genomic_data():
    if 'genomicFile' not in request.files:
        return 'No file part'
    file = request.files['genomicFile']
    if file.filename == '':
        return 'No selected file'

    file_path = "uploads/" + file.filename
    file.save(file_path)

    conditions_results = compare_gene_conditions(file_path, 'gene_conditions.csv')
    conditions_input = ", ".join(conditions_results)

    chatbot.conversation_chain.predict(
        input=f"My conditions due to my genomic data are as follows: {conditions_input}"
    )

    return 'File uploaded and analyzed successfully'

if __name__ == "__main__":
  app.run("0.0.0.0")