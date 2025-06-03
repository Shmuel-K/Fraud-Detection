# charts.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import html, dash_table


def create_category_chart(df: pd.DataFrame):
    if 'category' in df and 'amount' in df:
        summary = df.groupby('category')['amount'].sum().reset_index()
        fig = px.bar(summary, x='category', y='amount',
                     title='Transaction Amounts by Category')
        return fig.update_layout(template="plotly_dark")
    return px.bar(title='No data').update_layout(template="plotly_dark")


def create_pie_chart(df: pd.DataFrame):
    if 'category' in df and 'amount' in df:
        summary = df.groupby('category')['amount'].sum().reset_index()
        fig = px.pie(summary, names='category', values='amount',
                     title='Transactions Distribution by Category')
        return fig.update_layout(template="plotly_dark")
    return px.pie(title='No data').update_layout(template="plotly_dark")


def create_transaction_time_chart(df: pd.DataFrame):
    if 'step' in df:
        df2 = df.copy()
        df2['step'] = pd.to_numeric(df2['step'], errors='coerce')
        df2['hour'] = (df2['step'] - 1) % 24
        counts = df2.groupby('hour').size().reset_index(name='count')
        fig = px.bar(counts, x='hour', y='count',
                     title='Transactions by Hour', text='count')
        return fig.update_layout(template="plotly_dark")
    return px.bar(title='No data').update_layout(template="plotly_dark")


def create_fraud_customers_chart(df: pd.DataFrame):
    if 'fraud' in df and 'customer' in df:
        fdf = df[df['fraud'] == 1]
        top = fdf.groupby('customer').size().reset_index(name='count')\
                 .nlargest(10, 'count')
        fig = px.bar(top, x='customer', y='count',
                     title='Top 10 Fraud Customers', text='count')
        return fig.update_layout(template="plotly_dark")
    return px.bar(title='No data').update_layout(template="plotly_dark")


def create_suspicious_transaction_table(row_df: pd.DataFrame):
    return dash_table.DataTable(
        data=row_df.to_dict('records'),
        columns=[{"name": i, "id": i} for i in row_df.columns],
        style_table={'overflowX': 'auto'},
        style_header={'backgroundColor': '#333', 'color': '#FFF'},
        style_data={'backgroundColor': '#222', 'color': '#FFF'}
    )


def create_roc_curve():
    fpr = [0, 0.1, 0.3, 0.6, 1]
    tpr = [0, 0.4, 0.7, 0.9, 1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name='ROC Curve'))
    fig.add_trace(go.Scatter(x=[0,1], y=[0,1], mode='lines',
                             name='Random', line=dict(dash='dash')))
    return fig.update_layout(
        title='ROC Curve',
        xaxis_title='False Positive Rate',
        yaxis_title='True Positive Rate',
        template="plotly_dark"
    )


def create_performance_metrics_card():
    metrics = {"Accuracy":0.95,"Precision":0.92,"Recall":0.90,"F1-score":0.91,"ROC-AUC":0.96}
    items = [html.Li(f"{k}: {v:.2f}") for k,v in metrics.items()]
    return dbc.Card(dbc.CardBody([
        html.H5("Model Performance Metrics", className="card-title"),
        html.Ul(items),
        html.P("Key model performance metrics.", className="card-text")
    ]), className="mb-4")


def create_partition_diagram():
    labels = ["Raw Data","Features (X)","Target (y)","Step","Customer","Age",
              "Gender","ZipcodeOri","Merchant","ZipMerchant","Category","Amount","Fraud"]
    sources = [0,0] + [1]*10 + [2]
    targets = [1,2] + list(range(3,13))
    values  = [1]*len(sources)
    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=15, thickness=20, line=dict(color="black", width=0.5)),
        link=dict(source=sources, target=targets, value=values)
    ))
    return fig.update_layout(title_text="Data Partitioning", template="plotly_dark")
