########################### TEAM 7 ################################
## Jasmine Dickerson
## Samuel Hopkins
## Solomon Sledge
###################################################################

########################### SOURCES CITED ###########################
## Source: NBA Summer League playoffs Recap: Quaterfinals. (2016, July 17). Mountain West Connection. https://www.mwcconnection.com/2016/7/16/12207258/nba-summer-league-playoffs-recap-quaterfinals
## Source: Claude (for generating code/layout/text ideas and getting team logos, confirmed with/by Professor Schlosser)
## Source: Swar. (n.d.). GitHub - swar/nba_api: An API Client package to access the APIs for NBA.com. GitHub. https://github.com/swar/nba_api (for the API to gather data for CSV)
###################################################################

########################### AI USE ################################
## Used Claude to brainstorm project topic and page layout ideas.
## Used Claude to help download testing data into a CSV file.
## Used Claude for creating code for Dash styling ideas.
## Used Claude to help build visualization charts for each page.
## Used Claude to create callbacks for each graph to make charts interactive
# and dynamic for user.
## Used Claude to troubleshoot when errors occurred.
###################################################################

import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import gunicorn

#Setup App
#use_pages enables Dash's built-in multi-page routing (pages auto-register from /pages).
#suppress_callback_exceptions=True is required for multi-page apps since callback
#targets on other pages don't exist in the layout until that page is loaded.
#server = app.server is exposed for deployment
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True,
           title="BEYOND THE BOX SCORE", external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

#App Layout
#creates persistent navbar across all pages and dash.page_container
app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavLink("Power Rankings", href="/", active="exact"),
            dbc.NavLink("Efficiency Scale", href="/page1", active="exact"),
            dbc.NavLink("Team Trends", href="/page2", active="exact")
        ],
        brand="BEYOND THE BOX SCORE", color="#070096ff",
        fluid=True
    ), dash.page_container
])

#Run server
if __name__ == "__main__":
    app.run(debug=True)