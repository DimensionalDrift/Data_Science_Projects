import json
import pandas as pd
import plotly.express as px

# Load geojson from file, downloaded from:
# https://gist.github.com/eoiny/2183412
with open(
    "/home/chris/Projects/Data_Science/Project_corona_irl/data/ireland.json"
) as myfile:
    geojson = json.load(myfile)

# Load data from corona virus database
df = pd.read_csv(
    "http://opendata-geohive.hub.arcgis.com/datasets/d9be85b30d7748b5b7c09450b8aede63_0.csv"
)

# Print example of the dataframe and the geojson
print(geojson["features"][0])
print(df[0:26])

# Plot the figure
fig = px.choropleth_mapbox(
    df[0:26],
    geojson=geojson,
    color="PopulationCensus16",  # Data to be plotted
    locations="CountyName",  # Dataframe entry to match to geojson
    featureidkey="properties.county",  # GeoJSON entry to match to dataframe
    center={"lat": 53.5, "lon": -8.5},  # Center map display
    mapbox_style="carto-positron",
    zoom=6,
)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.show()
