import os
import sys
import time
import json
from datetime import datetime
from datetime import timedelta

import pandas as pd
import numpy as np
from tabulate import tabulate

import glob
import pickle

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go


# https://stackoverflow.com/questions/51063191/date-slider-with-plotly-dash-does-not-work
def unixTimeMillis(dt):
    """ Convert datetime to unix timestamp """
    return int(time.mktime(dt.timetuple()))


def unixToDatetime(unix):
    """ Convert unix timestamp to datetime. """
    return pd.to_datetime(unix, unit="s")


def getMarks(start, end, Nth=10):
    """ Returns the marks for labeling.
        Every Nth value will be used.
    """

    result = {}
    for i, date in enumerate(daterange):
        if i % Nth == 1:
            # Append value to dict
            result[unixTimeMillis(date)] = {
                "label": str(date.strftime("%m-%d")),
                "style": {"transform": "rotate(45deg)"},
            }

    return result


def noDataGraph():
    """
    Function to return a null graph object to be used where there is no
    data in the database
    """
    return {
        "layout": {
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 28},
                }
            ],
        }
    }


def dataframeLoader(online, local):
    # Load data from corona virus database
    try:
        # Try load the data directly from the virus database
        df = pd.read_csv(local)
    except:
        # If it fails to load then load the data from an archived copy
        # of the database
        print("Loading from file: %s" % local)
        df = pd.read_csv(local)

    return df


# Load geojson from file, downloaded from:
# https://gist.github.com/eoiny/2183412
with open(
    "/home/chris/Projects/Data_Science/Project_corona_irl/data/ireland.json"
) as myfile:
    geojson = json.load(myfile)


rooturl = "http://opendata-geohive.hub.arcgis.com/datasets/"
rootdir = "/home/chris/Projects/Data_Science/Project_corona_irl/data/"

# Load data from corona virus databases
df_county = dataframeLoader(
    rooturl + "d9be85b30d7748b5b7c09450b8aede63_0.csv",
    rootdir + "Covid19CountyStatisticsHPSCIreland.csv",
)

df_ireland = dataframeLoader(
    rooturl + "d8eb52d56273413b84b0187a4e9117be_0.csv",
    rootdir + "CovidStatisticsProfileHPSCIrelandOpenData.csv",
)

# pandas daterange of the maximum date range of the data is used as an
# input for the date slider
daterange = pd.date_range(
    start=df_county["TimeStamp"].iloc[0], end=df_county["TimeStamp"].iloc[-1], freq="D"
)

# An estimation of the number of known active cases of Covid-19 in the
# community. This number of calculated by taking the total number of
# active cases for a date and subtracting the total known cases from two
# weeks previous. This is based on the assumtion that all active cases
# from two weeks ago should be cured of the disease.
ealist = []
for i in range(len(df_ireland)):
    # If i is less than 14 then all active cases are considered still active
    if i < 14:
        ealist.append(df_ireland["TotalConfirmedCovidCases"].iloc[i])

    # Otherwise subtract the number of active cases from two weeks previous
    else:
        ealist.append(
            df_ireland["TotalConfirmedCovidCases"].iloc[i]
            - df_ireland["TotalConfirmedCovidCases"].iloc[i - 14]
        )

# Add the list of estimated active cases to the dataframe
df_ireland["EstimatedActiveCases"] = ealist


# Start the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Main layout of the dash app
app.layout = html.Div(
    [
        dbc.Row(
            # Col - width 12
            dbc.Col(
                [
                    # Title Card
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3(
                                    "Irish Covid-19 Data Dashboard",
                                    style={"text-align": "center", "margin": "0px"},
                                )
                            ]
                        ),
                        className="mt-3 ml-3",
                    ),
                ]
            )
        ),
        dbc.Row(
            [
                # Col - width 4
                dbc.Col(
                    [
                        # Total Stats Card
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Total Number of:", className="card-title",
                                    ),
                                    html.H1(
                                        "Cases %i"
                                        % df_ireland["TotalConfirmedCovidCases"].iloc[
                                            -1
                                        ],
                                        style={"text-align": "center"},
                                    ),
                                    html.H1(
                                        "Deaths %i"
                                        % df_ireland["TotalCovidDeaths"].iloc[-1],
                                        style={"text-align": "center"},
                                    ),
                                    html.P(
                                        html.Small(
                                            "as of %s"
                                            % df_ireland["Date"].iloc[-1][:10]
                                        ),
                                        style={"text-align": "right", "margin": "0px"},
                                    ),
                                ]
                            ),
                            className="mt-3 ml-3",
                        ),
                        # Totals Graph Card
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div(dcc.Graph(id="irl-totals")),
                                    html.Div(
                                        dcc.Dropdown(
                                            id="total-dropdown",
                                            options=[
                                                {
                                                    "label": "Total Confirmed Cases",
                                                    "value": "total",
                                                },
                                                {
                                                    "label": "Daily Confirmed Cases",
                                                    "value": "daily",
                                                },
                                                {
                                                    "label": "Estimate of Active Cases",
                                                    "value": "active",
                                                },
                                            ],
                                            value="total",
                                        )
                                    ),
                                ]
                            ),
                            className="mt-3 ml-3",
                        ),
                    ],
                    # width=12,
                    md=12,
                    lg=4,
                ),
                # Col - width 8
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                # Col - width 6
                                dbc.Col(
                                    [
                                        # Map Card
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.Div(dcc.Graph(id="irl-map",)),
                                                    html.Div(
                                                        dcc.Dropdown(
                                                            id="map-dropdown",
                                                            options=[
                                                                {
                                                                    "label": "Total Infections",
                                                                    "value": "total",
                                                                },
                                                                {
                                                                    "label": "Proportional Infections",
                                                                    "value": "proportional",
                                                                },
                                                            ],
                                                            value="total",
                                                        )
                                                    ),
                                                ]
                                            ),
                                            className="mt-3 ml-3 ml-lg-0",
                                        ),
                                    ],
                                    md=6,
                                    lg=6,
                                    className="px-lg-0",
                                ),
                                # Col - width 6
                                dbc.Col(
                                    [
                                        # Graph Card
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.Div(
                                                        dcc.Graph(id="irl-breakdown",)
                                                    ),
                                                    html.Div(
                                                        dcc.Dropdown(
                                                            id="breakdown-dropdown",
                                                            options=[
                                                                {
                                                                    "label": "Transmission",
                                                                    "value": "transmission",
                                                                },
                                                                {
                                                                    "label": "Gender",
                                                                    "value": "gender",
                                                                },
                                                                {
                                                                    "label": "Cases Age Profile",
                                                                    "value": "caseAge",
                                                                },
                                                                {
                                                                    "label": "Hospitalization Age Profile",
                                                                    "value": "hospitalAge",
                                                                },
                                                                {
                                                                    "label": "Likelihood of Hospitalization",
                                                                    "value": "hospitalOdds",
                                                                },
                                                            ],
                                                            value="transmission",
                                                        )
                                                    ),
                                                ]
                                            ),
                                            className="mt-3 ml-3",
                                        ),
                                    ],
                                    md=6,
                                    lg=6,
                                    className="pl-lg-0",
                                ),
                                # Col - width 12
                                dbc.Col(
                                    [
                                        # Slider Card
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.P(
                                                        id="slider-output-container",
                                                        style={"text-align": "right"},
                                                        className="px-3",
                                                    ),
                                                    html.Div(
                                                        dcc.Slider(
                                                            id="map-slider",
                                                            min=unixTimeMillis(
                                                                daterange.min()
                                                            ),
                                                            max=unixTimeMillis(
                                                                daterange.max()
                                                            ),
                                                            marks=getMarks(
                                                                daterange.min(),
                                                                daterange.max(),
                                                                int(
                                                                    len(daterange) / 10
                                                                ),
                                                            ),
                                                            step=86400,
                                                            value=unixTimeMillis(
                                                                daterange.max()
                                                            ),
                                                        )
                                                    ),
                                                ]
                                            ),
                                            className="mt-3 ml-3 ml-lg-0",
                                        )
                                    ],
                                    width=12,
                                    className="pl-lg-0",
                                ),
                            ]
                        ),
                    ],
                    # xs=12,
                    md=12,
                    lg=8,
                ),
            ],
        ),
        dbc.Row(
            # Col - width 12
            dbc.Col(
                [
                    # Sources Card
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Sources:"),
                                html.Div(
                                    html.A(
                                        "https://data.gov.ie/dataset/covidstatisticsprofilehpscirelandopendata",
                                        href="https://data.gov.ie/dataset/covidstatisticsprofilehpscirelandopendata",
                                    ),
                                    className="pl-3",
                                ),
                                html.Div(
                                    html.A(
                                        "https://data.gov.ie/dataset/covid19countystatisticshpscireland",
                                        href="https://data.gov.ie/dataset/covid19countystatisticshpscireland",
                                    ),
                                    className="pl-3",
                                ),
                                html.Div(
                                    html.A(
                                        "https://gist.github.com/eoiny/2183412",
                                        href="https://gist.github.com/eoiny/2183412",
                                    ),
                                    className="pl-3",
                                ),
                                html.Div(
                                    html.A(
                                        "https://dash.plotly.com/",
                                        href="https://dash.plotly.com/",
                                    ),
                                    className="pl-3",
                                ),
                            ]
                        ),
                        className="my-3 ml-3",
                    ),
                ]
            )
        ),
    ],
)


@app.callback(
    dash.dependencies.Output("slider-output-container", "children"),
    [dash.dependencies.Input("map-slider", "value")],
)
def update_output(value):
    """
    Function to update the slider output container to let the user know
    what date was selected
    """
    return "Date Selected: {}".format(unixToDatetime(value).strftime("%m/%d"))


@app.callback(
    Output("irl-map", "figure"),
    [
        dash.dependencies.Input("map-slider", "value"),
        dash.dependencies.Input("map-dropdown", "value"),
    ],
)
def update_map_figure(slider, dropdown):
    """
    Function to build and return the map figure
    """

    df_slice = df_county[
        df_county["TimeStamp"].str.contains(unixToDatetime(slider).strftime("%Y/%m/%d"))
    ]

    # If there is no data for a given date then return a null graph object
    if len(df_slice) < 1:
        return noDataGraph()

    # This creates the warning "A value is trying to be set on a copy of
    # a slice from a DataFrame" but also creates the intended outcome of
    # creating a temporary entry to a slice of the dataframe so the
    # warning should be ignored
    pd.options.mode.chained_assignment = None
    df_slice["CovidOverPopulation"] = (
        df_slice["ConfirmedCovidCases"] / df_slice["PopulationCensus16"] * 100
    )
    pd.options.mode.chained_assignment = "warn"

    if dropdown == "total":
        fig = px.choropleth_mapbox(
            df_slice,
            geojson=geojson,
            color="ConfirmedCovidCases",  # Data to be plotted
            locations="CountyName",  # Dataframe entry to match to geojson
            featureidkey="properties.county",  # GeoJSON entry to match dataframe
            center={"lat": 53.45, "lon": -8},  # Center map display
            mapbox_style="carto-positron",
            zoom=5,
            labels={"ConfirmedCovidCases": "Total Cases"},
            range_color=(0, max(df_county["ConfirmedCovidCases"])),
        )
        fig.update_layout(title="Total Covid Cases", margin=dict(l=0, r=0, t=50, b=50))

    elif dropdown == "proportional":
        fig = px.choropleth_mapbox(
            df_slice,
            geojson=geojson,
            color="CovidOverPopulation",  # Data to be plotted
            locations="CountyName",  # Dataframe entry to match to geojson
            featureidkey="properties.county",  # GeoJSON entry to match dataframe
            center={"lat": 53.45, "lon": -8},  # Center map display
            mapbox_style="carto-positron",
            zoom=5,
            labels={"CovidOverPopulation": "% of population"},
            range_color=(0, max(df_slice["CovidOverPopulation"])),
        )
        fig.update_layout(
            title="Proportional Covid Cases", margin=dict(l=0, r=0, t=50, b=50)
        )

    elif dropdown == "proportional2":
        fig = px.choropleth_mapbox(
            df_slice,
            geojson=geojson,
            color="PopulationProportionCovidCases",  # Data to be plotted
            locations="CountyName",  # Dataframe entry to match to geojson
            featureidkey="properties.county",  # GeoJSON entry to match dataframe
            center={"lat": 53.45, "lon": -8},  # Center map display
            mapbox_style="carto-positron",
            zoom=5,
            labels={"PopulationProportionCovidCases": "per 100,000"},
            range_color=(0, max(df_slice["PopulationProportionCovidCases"])),
        )

        fig.update_layout(
            title="Proportional Covid Cases", margin=dict(l=0, r=0, t=50, b=50)
        )
    return fig


@app.callback(
    Output("irl-totals", "figure"), [dash.dependencies.Input("total-dropdown", "value")]
)
def update_total_figure(dropdown):

    def datesplit(date):
        return date.split(" ")[0].replace("2020/", "")

    df_ireland["Date"] = df_ireland["Date"].apply(datesplit)

    if dropdown == "total":
        fig = go.Figure(
            data=go.Scatter(
                x=df_ireland["Date"],
                y=df_ireland["TotalConfirmedCovidCases"],
                mode="lines+markers",
            ),
        )
        fig.update_layout(title="Total Covid Cases", margin=dict(l=0, r=0, t=50, b=50))

    elif dropdown == "daily":

        fig = go.Figure(
            data=go.Scatter(
                x=df_ireland["Date"],
                y=df_ireland["ConfirmedCovidCases"],
                mode="lines+markers",
                name="Known Cases",
            ),
        )
        fig.add_trace(
            go.Scatter(
                x=df_ireland["Date"],
                y=df_ireland["ConfirmedCovidCases"].rolling(3, min_periods=1).mean(),
                mode="lines+markers",
                name="3 Day Rolling Avg.",
            )
        )
        fig.update_layout(title="Daily Covid Cases", margin=dict(l=0, r=0, t=50, b=50))
    elif dropdown == "active":
        fig = go.Figure(
            go.Scatter(
                x=df_ireland["Date"],
                y=df_ireland["EstimatedActiveCases"],
                mode="lines+markers",
            )
        )
        fig.update_layout(
            title="Estimate of Active Covid Cases", margin=dict(l=0, r=0, t=50, b=50)
        )

    fig.update_layout(height=350, legend=dict(x=0.625, y=0.99))
    fig.update_xaxes(tickangle=45)
    return fig


@app.callback(
    Output("irl-breakdown", "figure"),
    [
        dash.dependencies.Input("breakdown-dropdown", "value"),
        dash.dependencies.Input("map-slider", "value"),
    ],
)
def update_breakdown_figure(dropdown, slider):

    df_ireland_slice = df_ireland[
        df_ireland["Date"].str.contains(unixToDatetime(slider).strftime("%m/%d"))
    ]

    # If there is no data for a given date then return a null graph object
    if len(df_ireland_slice) < 1:
        fig = noDataGraph()

    else:
        if dropdown == "transmission":
            data = [
                df_ireland_slice["CommunityTransmission"].iloc[-1],
                df_ireland_slice["CloseContact"].iloc[-1],
                df_ireland_slice["TravelAbroad"].iloc[-1],
            ]

            labels = ["Community", "Close Contact", "Travel Abroad"]
            title = "% Known Mode of Transmission"

        elif dropdown == "gender":
            data = [
                df_ireland_slice["Male"].iloc[-1],
                df_ireland_slice["Female"].iloc[-1],
                df_ireland_slice["Unknown"].iloc[-1],
            ]

            labels = ["Male", "Female", "Unknown"]
            title = "Gender"

        elif dropdown == "caseAge":
            data = [
                df_ireland_slice["Aged1"].iloc[-1],
                df_ireland_slice["Aged1to4"].iloc[-1],
                df_ireland_slice["Aged5to14"].iloc[-1],
                df_ireland_slice["Aged15to24"].iloc[-1],
                df_ireland_slice["Aged25to34"].iloc[-1],
                df_ireland_slice["Aged35to44"].iloc[-1],
                df_ireland_slice["Aged45to54"].iloc[-1],
                df_ireland_slice["Aged55to64"].iloc[-1],
                df_ireland_slice["Aged65up"].iloc[-1],
            ]

            labels = [
                "Aged >1",
                "Aged 1-4",
                "Aged 5-14",
                "Aged 15-24",
                "Aged 25-34",
                "Aged 35-44",
                "Aged 45-54",
                "Aged 55-64",
                "Aged 65+",
            ]
            title = "Case Age Profile"

        elif dropdown == "hospitalAge":
            data = [
                df_ireland_slice["HospitalisedAged5"].iloc[-1],
                df_ireland_slice["HospitalisedAged5to14"].iloc[-1],
                df_ireland_slice["HospitalisedAged15to24"].iloc[-1],
                df_ireland_slice["HospitalisedAged25to34"].iloc[-1],
                df_ireland_slice["HospitalisedAged35to44"].iloc[-1],
                df_ireland_slice["HospitalisedAged45to54"].iloc[-1],
                df_ireland_slice["HospitalisedAged55to64"].iloc[-1],
                df_ireland_slice["HospitalisedAged65up"].iloc[-1],
            ]

            labels = [
                "Aged 1-4",
                "Aged 5-14",
                "Aged 15-24",
                "Aged 25-34",
                "Aged 35-44",
                "Aged 45-54",
                "Aged 55-64",
                "Aged 65+",
            ]
            title = "Hospitalization Age Profile"

        elif dropdown == "hospitalOdds":

            def percenter(i, j, dp=2):
                return round((i / j) * 100, dp)

            data = [
                percenter(
                    df_ireland_slice["HospitalisedAged5"].iloc[-1],
                    df_ireland_slice["Aged1to4"].iloc[-1],
                ),
                percenter(
                    df_ireland_slice["HospitalisedAged5to14"].iloc[-1],
                    df_ireland_slice["Aged5to14"].iloc[-1],
                ),
                percenter(
                    df_ireland_slice["HospitalisedAged15to24"].iloc[-1],
                    df_ireland_slice["Aged15to24"].iloc[-1],
                ),
                percenter(
                    df_ireland_slice["HospitalisedAged25to34"].iloc[-1],
                    df_ireland_slice["Aged25to34"].iloc[-1],
                ),
                percenter(
                    df_ireland_slice["HospitalisedAged35to44"].iloc[-1],
                    df_ireland_slice["Aged35to44"].iloc[-1],
                ),
                percenter(
                    df_ireland_slice["HospitalisedAged45to54"].iloc[-1],
                    df_ireland_slice["Aged45to54"].iloc[-1],
                ),
                percenter(
                    df_ireland_slice["HospitalisedAged55to64"].iloc[-1],
                    df_ireland_slice["Aged55to64"].iloc[-1],
                ),
                percenter(
                    df_ireland_slice["HospitalisedAged65up"].iloc[-1],
                    df_ireland_slice["Aged65up"].iloc[-1],
                ),
            ]

            labels = [
                "Aged 1-4",
                "Aged 5-14",
                "Aged 15-24",
                "Aged 25-34",
                "Aged 35-44",
                "Aged 45-54",
                "Aged 55-64",
                "Aged 65+",
            ]
            title = "% Likelihood of Hospitalization by Age"

        if np.isnan(data).any():
            return noDataGraph()

        fig = go.Figure(
            data=[go.Bar(x=labels, y=data, text=data, textposition="outside",),],
        )
        fig.update_layout(title=title, margin=dict(l=0, r=0, t=50, b=50))

    return fig


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')
