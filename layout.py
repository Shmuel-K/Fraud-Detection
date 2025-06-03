# layout.py

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from charts import (
    create_performance_metrics_card,
    create_roc_curve,
    create_partition_diagram
)

upload_section = dbc.Card(
    dbc.CardBody([
        html.H5("Upload a Transactions File", className="card-title"),
        dcc.Upload(
            id='uploader',
            children=dbc.Button("Upload CSV", color="primary", className="mt-2"),
            style={"textAlign": "center"}
        ),
        html.Div(id='save-status', className="mt-3"),
        html.Div(id='suspicious-alert-div', className="mt-3")
    ]),
    className="mb-4"
)

data_table_card = dbc.Card(
    dbc.CardBody([
        html.H5("Transaction Data Table", className="card-title"),
        dash_table.DataTable(
            id='transaction-table',
            page_size=10,
            style_table={'overflowX':'auto'},
            style_header={'backgroundColor':'#333','color':'#FFF','border':'1px solid #444'},
            style_data={'backgroundColor':'#222','color':'#FFF','border':'1px solid #444'}
        )
    ]),
    className="mb-4"
)

graph_bar_card = dbc.Card(
    dbc.CardBody([
        html.H5("Transaction Amounts by Category", className="card-title"),
        dcc.Graph(id='category-chart'),
        html.P("Total amounts per category.", className="card-text")
    ]),
    className="mb-4"
)

graph_pie_card = dbc.Card(
    dbc.CardBody([
        html.H5("Transactions Distribution by Category", className="card-title"),
        dcc.Graph(id='pie-chart'),
        html.P("Proportion per category.", className="card-text")
    ]),
    className="mb-4"
)

graph_time_card = dbc.Card(
    dbc.CardBody([
        html.H5("Transactions by Hour", className="card-title"),
        dcc.Graph(id='transaction-time-chart'),
        html.P("Aggregated by hour.", className="card-text")
    ]),
    className="mb-4"
)

graph_fraud_cust_card = dbc.Card(
    dbc.CardBody([
        html.H5("Top 10 Fraud Customers", className="card-title"),
        dcc.Graph(id='fraud-customers-chart'),
        html.P("Customers with most fraud cases.", className="card-text")
    ]),
    className="mb-4"
)

tabs = dcc.Tabs(
    id="tabs",
    value="data_tab",
    children=[
        dcc.Tab(
            label="Transaction Analysis",
            value="data_tab",
            children=[
                dbc.Row(dbc.Col(graph_bar_card, md=8)),
                dbc.Row([
                    dbc.Col(graph_pie_card, md=6),
                    dbc.Col(graph_time_card, md=6)
                ]),
                dbc.Row(dbc.Col(graph_fraud_cust_card, md=12)),
                data_table_card
            ]
        ),
        dcc.Tab(
            label="Model Performance",
            value="model_tab",
            children=[
                dbc.Row([
                    dbc.Col(create_performance_metrics_card(), md=4),
                    dbc.Col(dcc.Graph(id='roc-curve', figure=create_roc_curve()), md=8)
                ]),
                dbc.Row(
                    dbc.Col(dcc.Graph(id='partition-diagram', figure=create_partition_diagram()), md=12)
                ),
                html.Div("ROC shows the model’s ability to discriminate fraud.", className="mt-2")
            ]
        )
    ]
)

layout = dbc.Container(
    [
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand("Transaction Analyzer", style={"fontSize":"24px"})
            ]),
            color="dark",
            dark=True,
            className="mb-4"
        ),
        upload_section,
        html.Div(id='suspicious-row-div'),
        tabs
    ],
    fluid=True
)
