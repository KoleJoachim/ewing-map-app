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

@app.route("/test")
def test():
    try:
        # Check if CSV file exists
        if not os.path.exists("final_df.csv"):
            return "Error: final_df.csv file not found in application root", 500
            
        # Try loading the data
        df = pd.read_csv("final_df.csv")
        print("CSV loaded successfully. Columns:", df.columns.tolist())
        
        return f"""
        <h1>Data Load Test</h1>
        <p>File found: final_df.csv</p>
        <p>Rows: {len(df)}</p>
        <p>Columns: {', '.join(df.columns)}</p>
        <p>Sample FIPS: {df['FIPS'].iloc[0] if 'FIPS' in df.columns else 'FIPS column missing'}</p>
        """
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/")
def index():
    try:
        # First check if CSV exists
        if not os.path.exists("final_df.csv"):
            return "Data file not found - contact administrator", 500
            
        # Get selected chemical from query parameter
        selected_chemical = request.args.get('chemical', default='Rate_per_1M')
        
        # Load and validate data
        final_df = pd.read_csv("final_df.csv")
        final_df["FIPS"] = final_df["FIPS"].astype(str).str.zfill(5)
        print("Data loaded. Columns:", final_df.columns.tolist())

        # Validate chemical parameter
        if selected_chemical not in final_df.columns:
            selected_chemical = 'Rate_per_1M'
            print("Falling back to default chemical column")

        # Load GeoJSON with timeout
        with urllib.request.urlopen(
            "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
            timeout=10
        ) as response:
            geojson_data = json.load(response)

        # Create choropleth map
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
        )

        # Update layout
        fig.update_layout(
            geo=dict(
                center={"lat": 37.8, "lon": -96},
                projection_scale=3  # Equivalent to zoom=3 in older versions
            ),
            title=f"{selected_chemical} Incidence by County",
            margin={"r":0,"t":40,"l":0,"b":0},
            height=700
        )

        # Generate HTML
        plot_html = pio.to_html(fig, full_html=False)
        
        # Build full page with dropdown
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Chemical Map</title>
        </head>
        <body>
            <select id="chemicalSelect" onchange="updateChemical(this.value)">
                <option value="Rate_per_1M" {"selected" if selected_chemical == "Rate_per_1M" else ""}>Rate per 1M</option>
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

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Critical Error: {error_trace}")
        return f"<pre>Server Error: {str(e)}\n\n{error_trace}</pre>", 500

# Production configuration - do not modify
if __name__ == "__main__":
    # This block will NOT be used in production
    app.run()
