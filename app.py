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
    """Dynamically identify chemical columns from CSV"""
    base_cols = ['FIPS', 'Count', 'Population', 'Rate_per_1M']
    df = pd.read_csv("final_df.csv", nrows=1)  # Read just headers
    return [col for col in df.columns if col not in base_cols and '_label' in col]

@app.route("/ping")
def ping():
    return "pong"

@app.route("/")
def index():
    try:
        # Load data with optimized types
        chem_columns = get_chemical_columns()
        dtype_dict = {col: 'float32' for col in chem_columns}
        dtype_dict.update({'FIPS': 'string', 'Population': 'int32'})
        
        final_df = pd.read_csv("final_df.csv", dtype=dtype_dict)
        final_df["FIPS"] = final_df["FIPS"].str.zfill(5)

        # Get selected chemical
        selected_chemical = request.args.get('chemical', 'Rate_per_1M')
        if selected_chemical not in final_df.columns:
            selected_chemical = 'Rate_per_1M'

        # Create choropleth
        fig = px.choropleth(
            final_df,
            geojson=GEOJSON,
            locations="FIPS",
            featureidkey="properties.FIPS",
            color=selected_chemical,
            color_continuous_scale="YlOrRd",
            range_color=(0, final_df[selected_chemical].max()),
        ).update_layout(
            geo=dict(center={"lat": 37.8, "lon": -96}, projection_scale=3),
            margin={"r":0,"t":40,"l":0,"b":0},
            height=700
        )

        # Generate HTML with dynamic dropdown
        plot_html = pio.to_html(fig, full_html=False)
        options = "\n".join(
            f'<option value="{col}" {"selected" if selected_chemical==col else ""}>'
            f'{col.replace("_label", "").title()}</option>'
            for col in ['Rate_per_1M'] + chem_columns
        )
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Chemical Exposure Map</title></head>
        <body>
            <select onchange="window.location.search=`chemical=${{this.value}}`">
                {options}
            </select>
            {plot_html}
        </body>
        </html>
        """

    except Exception as e:
        return f"""
        <h1>Error</h1>
        <p>{str(e)}</p>
        <p>Columns available: {', '.join(pd.read_csv('final_df.csv', nrows=1).columns)}</p>
        """, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port)
