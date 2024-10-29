from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/hello', methods=['POST'])
def hello():
    data = request.json
    input_text = data.get('text', '')
    output_text = input_text[::-1]  # Example: reverse the input text
    return jsonify({'output': output_text})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
