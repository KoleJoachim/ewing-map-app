import os
import gc
import json
import urllib.request
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, request

app = Flask(__name__)

# Load GeoJSON once at startup
with urllib.request.urlopen(
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    timeout=10
) as response:
    GEOJSON = json.load(response)

@app.route("/ping")
def ping():
    return "pong"

@app.route("/test")
def test():
    try:
        if not os.path.exists("final_df.csv"):
            return "CSV file missing", 500
            
        # Load with optimized data types
        df = pd.read_csv("final_df.csv", dtype={
            'FIPS': 'string',
            'Rate_per_1M': 'float32',
            'ChemicalA': 'float32',
            'ChemicalB': 'float32'
        })
        
        return f"""
        <h1>Data Test</h1>
        <p>Memory Usage: {df.memory_usage(deep=True).sum()/1e6:.2f} MB</p>
        <p>Rows: {len(df)}</p>
        <p>Columns: {', '.join(df.columns)}</p>
        """
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/")
def index():
    try:
        if not os.path.exists("final_df.csv"):
            return "Data file not found", 500

        # Load data with optimized types
        final_df = pd.read_csv("final_df.csv", dtype={
            'FIPS': 'string',
            'Rate_per_1M': 'float32',
            'ChemicalA': 'float32',
            'ChemicalB': 'float32'
        })
        final_df["FIPS"] = final_df["FIPS"].str.zfill(5)
        
        # Force garbage collection
        gc.collect()

        selected_chemical = request.args.get('chemical', 'Rate_per_1M')
        if selected_chemical not in final_df.columns:
            selected_chemical = 'Rate_per_1M'

        # Create choropleth
        fig = px.choropleth(
            final_df,
            geojson=GEOJSON,  # Use preloaded GeoJSON
            locations="FIPS",
            featureidkey="properties.FIPS",
            color=selected_chemical,
            color_continuous_scale="YlOrRd",
            range_color=(0, final_df[selected_chemical].max()),
        )

        fig.update_layout(
            geo=dict(
                center={"lat": 37.8, "lon": -96},
                projection_scale=3
            ),
            margin={"r":0,"t":40,"l":0,"b":0},
            height=700
        )

        # Generate HTML
        plot_html = pio.to_html(fig, full_html=False)
        
        # Clean up memory
        fig = None
        gc.collect()

        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Chemical Map</title></head>
        <body>
            <select onchange="window.location.search=`chemical=${this.value}`">
                <option {'selected' if selected_chemical=='Rate_per_1M' else ''} 
                        value="Rate_per_1M">Rate per 1M</option>
                <option {'selected' if selected_chemical=='ChemicalA' else ''} 
                        value="ChemicalA">Chemical A</option>
                <option {'selected' if selected_chemical=='ChemicalB' else ''} 
                        value="ChemicalB">Chemical B</option>
            </select>
            {plot_html}
        </body>
        </html>
        """

    except Exception as e:
        import traceback
        error = f"<pre>Error: {str(e)}\n\n{traceback.format_exc()}</pre>"
        return error, 500

if __name__ == "__main__":
    app.run()
