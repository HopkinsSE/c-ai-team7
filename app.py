########################### AI USE ################################
## Used Claude to brainstorm project topic and page layout ideas
## Used Claude to help download testing data into a CSV file
## Used Claude for creating code for Dash styling ideas
## Used Claude to help build visualization charts for each page
###################################################################

import requests
import datetime as dt
import pandas as pd
import dash
from dash import Dash, html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc


app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True,
           title="Assistant Coach Recruitment Hub", external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavLink("Power Rankings", href="/", active="exact"),
            dbc.NavLink("Efficiency Scale", href="/page1", active="exact"),
            dbc.NavLink("Team Trends", href="/page2", active="exact")
        ],
        brand="Coaching Assistant Dashboard", color="#070096ff",
        fluid=True
    ), dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)