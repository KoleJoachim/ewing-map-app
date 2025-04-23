from flask import Flask
import os
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    df = pd.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"]
    })
    html_table = df.to_html(index=False)
    return f"<h1>✅ Plotting Test</h1>{html_table}"

@app.route("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    print(f"✅ Flask is starting on port {port}")
    app.run(host="0.0.0.0", port=port)
