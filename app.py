from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Flask is working"

@app.route("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    print(f"✅ Flask is starting on port {port}")
    app.run(host="0.0.0.0", port=port)
