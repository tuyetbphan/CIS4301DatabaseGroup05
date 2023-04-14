from flask import Blueprint, render_template, config, request
from plotly.subplots import make_subplots
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
import oracledb
import numpy as np

connection = oracledb.connect(
    user = "natalie.valcin",
    password= "umGb8Uul71wMtOTXtLQPzyIG",
    dsn = "oracle.cise.ufl.edu/orcl",
    port = "1521"
)

print("Do we have a good connection: ", connection.is_healthy())
print("Are we using a Thin connection: ", connection.thin)
print("Database version: ", connection.version)




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
    cursor = connection.cursor()
    cursor.execute("""
    SELECT Area_Name, EXTRACT(YEAR FROM Date_) AS year, EXTRACT(MONTH FROM Date_) AS month,
    COUNT(*) AS total_crimes
    FROM gongbingwong.crime
    WHERE Date_ >= TO_DATE('01-JAN-10', 'DD-MON-YY') AND Date_ <= TO_DATE('27-MAR-23', 'DD-MON-YY')
    GROUP BY Area_Name, EXTRACT(YEAR FROM Date_), EXTRACT(MONTH FROM Date_)
    ORDER BY Area_Name, year, month
    """)
    query_results = cursor.fetchall()
   
    df = pd.DataFrame(query_results, columns=['Area_Name', 'Year', 'Month', 'Total_Crimes'])
    df['Year'] = pd.to_datetime(df['Year'], format='mixed')
    df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
    df_pivot = df.pivot(index='Date', columns='Area_Name', values='Total_Crimes')
    df_pivot.ffill(axis=0, inplace=True)
    df_pivot.reset_index(inplace=True)
    df_melted = pd.melt(df_pivot, id_vars='Date', value_vars=df['Area_Name'].unique(), value_name='Total_Crimes', var_name='Area_Name')
    fig = px.line(df_melted, x='Date', y='Total_Crimes', color='Area_Name', title='Total Crimes by Month')

    print(fig.data[0])
    fig_data = fig.to_html(full_html=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # fig.show()

    return render_template("querythree.html", graphJSON=graphJSON)


@app_blueprint.route('/queryfour')
def queryfour():
    # cursor = connection.cursor()

    # # do something like fetch, insert, etc.
    # # cursor.execute("SELECT * FROM TPHAN1.COVID_19")
    # # cursor.execute("SELECT * FROM TPHAN1.PATIENT")
    # # cursor.execute("SELECT * FROM GONGBINGWONG.CRIME")
    # # cursor.execute("SELECT * FROM GONGBINGWONG.VICTIM")
    # # cursor.execute("SELECT CASE_ID FROM TPHAN1.COVID_19 WHERE CASE_DATE = '01-NOV-20' AND WHERE ")
    # # cursor.execute("SELECT CASE_ID, COUNT(*) FROM TPHAN1.COVID_19 WHERE CURRENT_STATUS = 'PROBABLE CASE'")
    # # cursor.execute("SELECT * FROM TPHAN1.PATIENT")

    # sqlTxt = "SELECT DISTINCT CRIME_CODE_1 FROM GONGBINGWONG.CRIME"
    # cursor.execute(sqlTxt)

    # records = cursor.fetchall()
    # records = list(records)

    # # for record in records:
    # #     print(record)

    # fig = go.Figure(
    #     data=[go.Bar(y=records)],
    #     layout_title_text="A Figure Displayed with fig.show()"
    # )
    # fig.show()


    # cursor.close()
    # connection.close() 
    return render_template("queryfour.html")


@app_blueprint.route('/queryfive')
def queryfive():
    return render_template("queryfive.html")



# this was a way to see if I can create dash-like graphs without Dash; only using flask and plotly
@app_blueprint.route('/callback', methods=['POST', 'GET'])
def cb():
    return gm(request.args.get('data'))

@app_blueprint.route('/callback2', methods=['POST', 'GET'])
def cback():
    return queryfive()

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





