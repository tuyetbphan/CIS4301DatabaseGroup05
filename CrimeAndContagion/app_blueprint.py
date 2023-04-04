from flask import Blueprint, render_template, config, request
from plotly.subplots import make_subplots
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go

app_blueprint = Blueprint('app_blueprint', __name__)

@app_blueprint.route('/')
def homepage():
    return render_template("homepage.html")

@app_blueprint.route('/queryone')
def queryone():
    return render_template("queryone.html", graphJSON=gm())


@app_blueprint.route('/querytwo')
def querytwo():
    return render_template("querytwo.html", graphJSON=dy())


@app_blueprint.route('/querythree')
def querythree():
    return render_template("querythree.html")


@app_blueprint.route('/queryfour')
def queryfour():
    return render_template("queryfour.html")


@app_blueprint.route('/queryfive')
def queryfive():
    return render_template("queryfive.html")


@app_blueprint.route('/customquery')
def customquery():
    return render_template("customquery.html")

# this was a way to see if I can create dash-like graphs without Dash; only using flask and plotly
@app_blueprint.route('/callback', methods=['POST', 'GET'])
def cb():
    return gm(request.args.get('data'))

@app_blueprint.route('/callback2', methods=['POST', 'GET'])
def cback():
    return dy()

def gm(country='United Kingdom'):
    df = pd.DataFrame(px.data.gapminder())

    fig = px.line(df[df['country'] == country], x="year", y="gdpPercap")

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    print(fig.data[0])

    return graphJSON


def dy():
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=[1, 2, 3], y=[40, 50, 60], name="yaxis data"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=[2, 3, 4], y=[4, 5, 6], name="yaxis2 data"),
        secondary_y=True,
    )

    # Add figure title
    fig.update_layout(
        title_text="Double Y Axis Example"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="xaxis title")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
    fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # fig.show()    
    return graphJSON


