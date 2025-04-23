from flask import Flask
import pandas as pd
import plotly.express as px
import plotly.io as pio
import json
import urllib.request
import os

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "pong"

@app.route("/")
def index():
    print("🔄 / route was accessed")

    final_df = pd.read_csv("final_df.csv")
    final_df["FIPS"] = final_df["FIPS"].astype(str).str.zfill(5)

    with urllib.request.urlopen("https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json") as response:
        geojson_data = json.load(response)

    pastel_colors = {
        "Xylene (Mixed Isomers)": "#a6cee3",
        "Ethylbenzene": "#fdbf6f",
        "Toluene": "#b2df8a",
        "Naphthalene": "#fb9a99",
        "Nickel compounds": "#cab2d6",
        "Benzo[g,h,i]perylene": "#ffff99"
    }

    chemical_column_map = {
        "Xylene (Mixed Isomers)": "xylene (mixed isomers)_label",
        "Ethylbenzene": "ethylbenzene_label",
        "Toluene": "toluene_label",
        "Naphthalene": "naphthalene_label",
        "Nickel compounds": "nickel compounds_label",
        "Benzo[g,h,i]perylene": "benzo[g,h,i]perylene_label"
    }

    overlay_traces = []
    for chem, color in pastel_colors.items():
        label_col = chemical_column_map[chem]
        if label_col in final_df.columns:
            chem_df = final_df[final_df[label_col] == "High"].copy()
            chem_df["Exposure"] = chem
            trace = px.choropleth_mapbox(
                chem_df,
                geojson=geojson_data,
                locations="FIPS",
                color_discrete_sequence=[color],
                mapbox_style="carto-positron",
                zoom=3,
                center={"lat": 37.8, "lon": -96},
                opacity=0.7,
                hover_name="Exposure"
            ).update_traces(
                marker_line_width=1,
                marker_line_color=color,
                name=chem,
                showlegend=True
            ).data[0]
            overlay_traces.append(trace)

    fig = px.choropleth_mapbox(
        final_df,
        geojson=geojson_data,
        locations="FIPS",
        color="Rate_per_1M",
        color_continuous_scale="YlOrRd",
        range_color=(0, final_df["Rate_per_1M"].max()),
        mapbox_style="carto-positron",
        zoom=3,
        center={"lat": 37.8, "lon": -96},
        opacity=0.5,
        labels={"Rate_per_1M": "Ewing Rate per 1M"},
        hover_name="FIPS"
    )

    for trace in overlay_traces:
        fig.add_trace(trace)

    fig.update_layout(
        title="Ewing Sarcoma Incidence with Overlays of High Exposure to Statistically Significant Chemicals",
        legend_title_text="High Exposure Chemical",
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="left", x=0.01,
            bgcolor="white",
            bordercolor="black",
            borderwidth=0.5
        ),
        margin={"r":0,"t":40,"l":0,"b":0}
    )

    return pio.to_html(fig, full_html=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    print(f"✅ Flask is starting on port {port}")
    app.run(host="0.0.0.0", port=port)
