import os
import json
import urllib.request
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, request

app = Flask(__name__)

# Cache GeoJSON at startup
with urllib.request.urlopen(
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    timeout=10
) as response:
    GEOJSON = json.load(response)

def get_chemical_columns():
    """Classify columns based on data type"""
    df = pd.read_csv("cleaned_final_df.csv", nrows=1)
    numerical = ["Rate_per_1M", "Count", "Population"]
    categorical = [col for col in df.columns 
                 if col.endswith("_label") and col != "FIPS"]
    return numerical, categorical

@app.route("/ping")
def health_check():
    """Render health check endpoint"""
    return "pong", 200

@app.route("/")
def index():
    try:
        numerical_cols, categorical_cols = get_chemical_columns()
        selected_chemical = request.args.get("chemical", "Rate_per_1M")
        
        # Load data with proper types and null handling
        dtype = {"FIPS": "string"}
        final_df = pd.read_csv(
            "cleaned_final_df.csv",
            dtype=dtype
        ).fillna(0)
        
        # Ensure FIPS codes are 5-digit strings
        final_df["FIPS"] = final_df["FIPS"].str.zfill(5)

        # Validate chemical selection
        if selected_chemical not in numerical_cols + categorical_cols:
            selected_chemical = "Rate_per_1M"

        # Create visualization
        if selected_chemical in numerical_cols:
            fig = px.choropleth(
                final_df,
                geojson=GEOJSON,
                locations="FIPS",
                color=selected_chemical,
                color_continuous_scale="YlOrRd",
                range_color=(0, final_df[selected_chemical].quantile(0.95)),
            )
        else:
            # Handle categorical (0/1) data
            fig = px.choropleth(
                final_df,
                geojson=GEOJSON,
                locations="FIPS",
                color=selected_chemical.astype("category"),
                color_discrete_map={0: "green", 1: "red"},
                category_orders={selected_chemical: [0, 1]},
            )

        fig.update_layout(
            geo=dict(center={"lat": 37.8, "lon": -96}, projection_scale=3),
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            height=700
        )

        # Generate dropdown options
        options = "\n".join(
            f'<option value="{col}" {"selected" if col==selected_chemical else ""}>'
            f'{col.replace("_label", "").title().replace("]", "］").replace("[", "［")}</option>'
            for col in numerical_cols + categorical_cols
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Chemical Exposure Map</title></head>
        <body>
            <select onchange="window.location.search=`chemical=${{this.value}}`">
                {options}
            </select>
            {pio.to_html(fig, full_html=False)}
        </body>
        </html>
        """

    except Exception as e:
        return f"""
        <h1>Application Error</h1>
        <p>{str(e)}</p>
        <p>Common fixes:</p>
        <ul>
            <li>Ensure cleaned_final_df.csv exists</li>
            <li>Check column names in the CSV</li>
            <li>Verify FIPS codes are 5-digit strings</li>
        </ul>
        """, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
