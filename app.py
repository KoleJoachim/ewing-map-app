import os
import json
import urllib.request
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, request
from urllib.parse import unquote

PORT = int(os.environ.get("PORT", 8050)) 
app = Flask(__name__)

# Cache GeoJSON
with urllib.request.urlopen(
    "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    timeout=10
) as response:
    GEOJSON = json.load(response)

def load_optimized_data():
    """Load data with proper NaN handling"""
    df = pd.read_csv(
        "cleaned_final_proper.csv",
        dtype={"FIPS": "string"},
        na_values=['', 'nan', 'NaN']
    )
    
    # Clean FIPS (fill only FIPS NaNs)
    df["FIPS"] = df["FIPS"].fillna("00000").str.zfill(5)
    
    return df

# Load data once at startup
FINAL_DF = load_optimized_data()

def get_chemical_columns():
    """Get column lists with proper handling"""
    numerical = ["Rate_per_1M", "Count", "Population"]
    categorical = [col for col in FINAL_DF.columns 
                 if '_label' in col and FINAL_DF[col].isin([0, 1]).any()]
    return numerical, categorical

@app.route("/ping")
def health_check():
    return "pong", 200

@app.route("/")
def index():
    try:
        numerical_cols, categorical_cols = get_chemical_columns()
        selected_chemical = unquote(request.args.get("chemical", "Rate_per_1M"))
        
        # Validate selection
        if selected_chemical not in numerical_cols + categorical_cols:
            selected_chemical = "Rate_per_1M"

        # Filter data for visualization
        viz_df = FINAL_DF.copy()
        if selected_chemical in categorical_cols:
            # Remove rows without valid data for selected chemical
            viz_df = viz_df.dropna(subset=[selected_chemical])

        # Create visualization
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
                color=selected_chemical.astype('category'),
                color_discrete_map={0: "green", 1: "red"},
                category_orders={selected_chemical: [0, 1]},
            )

        fig.update_layout(
            geo=dict(center={"lat": 37.8, "lon": -96}, projection_scale=3),
            margin={"r": 0, "t": 40, "l": 0, "b": 0},
            height=700
        )

        # Generate dropdown options with cleaned names
        options = "\n".join(
            f'<option value="{col}" {"selected" if col==selected_chemical else ""}>'
            f'{col.replace("_label", "").replace("[", "(").replace("]", ")").replace("_", " ").title()}</option>'
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
        <h1>Error</h1>
        <p>{str(e)}</p>
        <p>Try selecting a different chemical or refreshing the page.</p>
        """, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
