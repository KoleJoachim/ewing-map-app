import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import urllib.request
import os

# Load data
final_df = pd.read_csv("final_df.csv")
final_df["FIPS"] = final_df["FIPS"].astype(str).str.zfill(5)

# GeoJSON for counties
with urllib.request.urlopen("https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json") as response:
    counties_geojson = json.load(response)

# Set up Dash app
app = Dash(__name__)

# Dropdown options and colors
chem_options = {
    "nickel_label": "Nickel",
    "chromium_label": "Chromium",
    "benzo[g,h,i]perylene_label": "Benzo[g,h,i]perylene"
}

chem_colors = {
    "nickel_label": "#636EFA",       # Blue
    "chromium_label": "#EF553B",     # Red
    "benzo[g,h,i]perylene_label": "#00CC96"  # Green
}

# Layout
app.layout = html.Div([
    html.H2("Ewing Sarcoma Incidence and Chemical Exposure Explorer"),
    html.Label("Toggle high exposure overlays below:"),
    dcc.Checklist(
        id="chemical-checklist",
        options=[{"label": name, "value": key} for key, name in chem_options.items()],
        value=list(chem_options.keys()),
        inline=True
    ),
    dcc.Graph(id="choropleth-map")
])

# Callback to update map
@app.callback(
    Output("choropleth-map", "figure"),
    Input("chemical-checklist", "value")
)
def update_map(selected_chems):
    # Base choropleth
    fig = px.choropleth_mapbox(
        final_df,
        geojson=counties_geojson,
        locations="FIPS",
        color="Rate_per_1M",
        color_continuous_scale="YlOrRd",
        range_color=(0, final_df["Rate_per_1M"].max()),
        mapbox_style="carto-positron",
        zoom=3,
        center={"lat": 37.8, "lon": -96},
        opacity=0.6,
        labels={"Rate_per_1M": "Ewing Rate per 1M"}
    )

    # Add overlays
    for chem in selected_chems:
        overlay = final_df[final_df[chem] == "High"]
        fig.add_choroplethmapbox(
            geojson=counties_geojson,
            locations=overlay["FIPS"],
            z=[1] * len(overlay),
            colorscale=[[0, chem_colors[chem]], [1, chem_colors[chem]]],
            showscale=False,
            marker_line_width=1,
            marker_line_color="white",
            name=chem_options[chem]
        )

    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, legend_title="High Exposure Chemical")
    return fig

# Run the app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
