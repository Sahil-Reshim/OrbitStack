from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(status="healthy", service="auth")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)