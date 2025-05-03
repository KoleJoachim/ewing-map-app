import os
import pandas as pd
import json
import urllib.request
import plotly.express as px
import plotly.io as pio
from flask import Flask, request

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong"

@app.route("/")
def index():
    print("🔄 / route accessed")
    
    # Get selected chemical from query parameter
    selected_chemical = request.args.get('chemical', default='Rate_per_1M')
    
    # Load data
    final_df = pd.read_csv("final_df.csv")
    final_df["FIPS"] = final_df["FIPS"].astype(str).str.zfill(5)

    # Check if selected_chemical exists in the dataframe
    if selected_chemical not in final_df.columns:
        selected_chemical = 'Rate_per_1M'  # default to existing column

    # Load GeoJSON
    with urllib.request.urlopen("https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json") as response:
        geojson_data = json.load(response)

    # Create choropleth
    fig = px.choropleth(
        final_df,
        geojson=geojson_data,
        locations="FIPS",
        featureidkey="properties.FIPS",
        color=selected_chemical,
        color_continuous_scale="YlOrRd",
        range_color=(0, final_df[selected_chemical].max()),
        hover_name="FIPS",
        labels={selected_chemical: f"{selected_chemical} per 1M"},
        center={"lat": 37.8, "lon": -96},
        zoom=3,
    )

    fig.update_layout(
        title=f"{selected_chemical} Incidence by County",
        margin={"r":0,"t":40,"l":0,"b":0},
        height=700
    )

    # Generate HTML with dropdown
    plot_html = pio.to_html(fig, full_html=False)
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chemical Map</title>
    </head>
    <body>
        <select id="chemicalSelect" onchange="updateChemical(this.value)">
            <option value="Rate_per_1M" {"selected" if selected_chemical == "Rate_per_1M" else ""}>Rate per 1M</option>
            <!-- Add other chemical options here based on your CSV columns -->
            <option value="ChemicalA" {"selected" if selected_chemical == "ChemicalA" else ""}>Chemical A</option>
            <option value="ChemicalB" {"selected" if selected_chemical == "ChemicalB" else ""}>Chemical B</option>
        </select>
        {plot_html}
        <script>
            function updateChemical(chemical) {{
                window.location.search = `chemical=${{chemical}}`;
            }}
        </script>
    </body>
    </html>
    """
    return full_html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    print(f"✅ Flask is starting on port {port}")
    app.run(host="0.0.0.0", port=port)
