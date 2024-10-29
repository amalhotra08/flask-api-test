from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/greet', methods=['POST'])
def greet():
    data = request.json
    text = data.get('text', '')
    return jsonify({"message": f"Hello {text}"}), 200

if __name__ == '__main__':
    app.run(debug=True)

