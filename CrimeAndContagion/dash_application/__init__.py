import dash
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd


# created 'dash_application' folder to essentially run a dash application inside a flask application

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame(
    {
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"],
    }
)


def create_dash_application(flask_app):
    dash_app = dash.Dash(server=flask_app, name="Dashboard", url_base_pathname="/dash/")
    dash_app.layout = html.Div(
        children=[
            html.H1(children="Hello Dash"),
            html.Div(
                children="""
            Dash: A web application framework for Python.
        """
            ),
            dcc.Graph(
                id="example-graph",
                figure=px.bar(df, x="Fruit", y="Amount", color="City", barmode="group"),
            ),
        ]
    )

    return dash_app