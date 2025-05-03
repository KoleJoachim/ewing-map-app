import os
import gc
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
    """Separate numerical and categorical columns"""
    base_cols = ['FIPS', 'Count', 'Population', 'Rate_per_1M']
    df = pd.read_csv("final_df.csv", nrows=1)
    
    categorical = [col for col in df.columns 
                 if col not in base_cols and '_label' in col]
    numerical = ['Rate_per_1M']  # Add other numerical columns if available
    
    return numerical, categorical

@app.route("/")
def index():
    try:
        numerical_cols, categorical_cols = get_chemical_columns()
        selected_chemical = request.args.get('chemical', 'Rate_per_1M')
        
        # Load data with proper types
        dtype = {
            'FIPS': 'string',
            'Population': 'int32',
            'Count': 'int32',
            **{col: 'category' for col in categorical_cols}
        }
        final_df = pd.read_csv("final_df.csv", dtype=dtype)
        final_df["FIPS"] = final_df["FIPS"].str.zfill(5)

        # Validate selection
        if selected_chemical not in numerical_cols + categorical_cols:
            selected_chemical = 'Rate_per_1M'

        # Create appropriate visualization
        if selected_chemical in numerical_cols:
            fig = px.choropleth(
                final_df,
                geojson=GEOJSON,
                locations="FIPS",
                color=selected_chemical,
                color_continuous_scale="YlOrRd",
                range_color=(0, final_df[selected_chemical].max()),
            )
        else:  # Categorical data
            fig = px.choropleth(
                final_df,
                geojson=GEOJSON,
                locations="FIPS",
                color=selected_chemical,
                color_discrete_sequence=px.colors.sequential.YlOrRd,
            )

        fig.update_layout(
            geo=dict(center={"lat": 37.8, "lon": -96}, projection_scale=3),
            margin={"r":0,"t":40,"l":0,"b":0},
            height=700
        )

        # Generate dropdown options
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
        return f"""
        <h1>Error</h1>
        <p>{str(e)}</p>
        <p>Ensure you're selecting numerical columns for quantitative analysis.
        Categorical columns (ending with _label) show risk levels.</p>
        """, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
