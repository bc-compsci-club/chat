from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import cross_origin, CORS
from chat import Chat

load_dotenv()
app = Flask(__name__)
chat = Chat()
CORS(app)

@app.route("/api/v1/llm", methods=["POST"])
@cross_origin(supports_credentials=True, origins="http://localhost:3000")
def hello_world():
    content = (request.json[-1]["content"])
    def generate():
        for response in chat.response(content):
            yield response
    return generate()

if __name__ == "__main__":
    app.run(debug=True)


