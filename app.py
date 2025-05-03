import os
import json
import urllib.request
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, request
from functools import lru_cache

app = Flask(__name__)

# Cache GeoJSON at startup
with urllib.request.urlopen(
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    timeout=10
) as response:
    GEOJSON = json.load(response)

@lru_cache(maxsize=None)
def load_and_optimize_data():
    """Load and optimize data once with memory-efficient types"""
    try:
        dtype = {"FIPS": "string"}
        df = pd.read_csv(
            "cleaned_final_df.csv",
            dtype=dtype,
            usecols=lambda col: col != "Unnamed: 0"  # Skip index column if present
        )
        
        # Convert to categorical where possible
        categorical_cols = [col for col in df.columns if col.endswith("_label")]
        df[categorical_cols] = df[categorical_cols].astype("category")
        
        # Optimize numerical columns
        num_cols = ["Count", "Population", "Rate_per_1M"]
        df[num_cols] = df[num_cols].apply(pd.to_numeric, downcast="unsigned")
        
        # Clean FIPS codes
        df["FIPS"] = df["FIPS"].str.zfill(5).fillna("00000")
        
        return df
    except Exception as e:
        app.logger.error(f"Data loading failed: {str(e)}")
        raise

# Load data once at startup
try:
    FINAL_DF = load_and_optimize_data()
except Exception as e:
    app.logger.critical(f"Critical startup failure: {str(e)}")
    raise

def get_chemical_columns():
    """Get column lists from cached data"""
    numerical = ["Rate_per_1M", "Count", "Population"]
    categorical = [col for col in FINAL_DF.columns 
                 if col.endswith("_label") and col != "FIPS"]
    return numerical, categorical

@app.route("/ping")
def health_check():
    """Lightweight health check"""
    return "pong", 200

@app.route("/")
def index():
    try:
        numerical_cols, categorical_cols = get_chemical_columns()
        selected_chemical = request.args.get("chemical", "Rate_per_1M")

        # Validate selection
        if selected_chemical not in numerical_cols + categorical_cols:
            selected_chemical = "Rate_per_1M"

        # Create visualization with sampled data
        viz_df = FINAL_DF.sample(n=1000) if len(FINAL_DF) > 5000 else FINAL_DF
        
        if selected_chemical in numerical_cols:
            fig = px.choropleth(
                viz_df,
                geojson=GEOJSON,
                locations="FIPS",
                color=selected_chemical,
                color_continuous_scale="YlOrRd",
                range_color=(0, viz_df[selected_chemical].quantile(0.95)),
            )
        else:
            fig = px.choropleth(
                viz_df,
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

        options = "\n".join(
            f'<option value="{col}" {"selected" if col==selected_chemical else ""}>'
            f'{col.replace("_label", "").title()}</option>'
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
        app.logger.error(f"Route error: {str(e)}")
        return f"""
        <h1>Application Error</h1>
        <p>{str(e)}</p>
        <p>Common fixes:</p>
        <ul>
            <li>Try refreshing the page</li>
            <li>Select a different chemical parameter</li>
            <li>Contact support if this persists</li>
        </ul>
        """, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
