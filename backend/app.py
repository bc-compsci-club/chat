from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import cross_origin


load_dotenv()
from chat import Chat

chat = Chat()


app = Flask(__name__)

@app.route("/api/v1/llm", methods=["POST"])
@cross_origin(supports_credentials=True, origins="http://localhost:3000")
def hello_world():
    content = (request.json[-1]["content"])
    response = chat.response(content)
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)


