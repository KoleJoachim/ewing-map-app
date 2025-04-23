import os
import pandas as pd
import json
import urllib.request
import plotly.express as px
import plotly.io as pio
from flask import Flask

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong"

@app.route("/")
def index():
    print("🔄 / route accessed")
    
    # Load your data dynamically
    final_df = pd.read_csv("final_df.csv")
    final_df["FIPS"] = final_df["FIPS"].astype(str).str.zfill(5)

    # Load counties GeoJSON (for choropleth_map)
    with urllib.request.urlopen("https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json") as response:
        geojson_data = json.load(response)

    # Create a simple MapLibre-compatible choropleth
    fig = px.choropleth_map(
        final_df,
        geojson=geojson_data,
        locations="FIPS",
        featureidkey="properties.FIPS",
        color="Rate_per_1M",
        color_continuous_scale="YlOrRd",
        range_color=(0, final_df["Rate_per_1M"].max()),
        hover_name="FIPS",
        labels={"Rate_per_1M": "Ewing Rate per 1M"},
        center={"lat": 37.8, "lon": -96},
        zoom=3,
    )

    fig.update_layout(
        title="Ewing Sarcoma Incidence by County",
        margin={"r":0,"t":40,"l":0,"b":0},
        height=700
    )

    return pio.to_html(fig, full_html=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    print(f"✅ Flask is starting on port {port}")
    app.run(host="0.0.0.0", port=port)
