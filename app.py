# app.py

from flask import Flask
import dash
from dash import dcc
import dash_bootstrap_components as dbc

from layout import layout
from server import register_api_routes
from callbacks import register_callbacks

# 1) Flask + API
server = Flask(__name__)
register_api_routes(server)

# 2) Dash setup
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.CYBORG])
app.config.suppress_callback_exceptions = True

# Wrap the entire layout in a Loading spinner
app.layout = dcc.Loading(
    id="global-loading",
    type="circle",      # a circular spinner
    fullscreen=True,    # covers the whole screen
    children=layout
)

# 3) Callbacks
register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
