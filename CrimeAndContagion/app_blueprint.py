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

# Query 1: How have the crimes of theft, assault, and vandalism developed over time? 
@app_blueprint.route('/queryone')
def queryone():
    cursor = connection.cursor()
    cursor.execute("""
    SELECT 
        CRIME_CODE_DESCRIPTION, 
        TO_CHAR(Date_, 'MON-YY') as month,
        COUNT(*) as num_crimes,
        ROUND(100 * (COUNT(*) - LAG(COUNT(*)) 
        OVER (PARTITION BY CRIME_CODE_DESCRIPTION 
        ORDER BY MIN(Date_))) / NVL(LAG(COUNT(*)) 
        OVER (PARTITION BY CRIME_CODE_DESCRIPTION 
        ORDER BY MIN(Date_)), 1), 3) as percent_change
    FROM 
        GONGBINGWONG.Crime
    WHERE 
        CRIME_CODE_DESCRIPTION LIKE '%THEFT%' OR 
        CRIME_CODE_DESCRIPTION LIKE '%ASSAULT%' OR
        CRIME_CODE_DESCRIPTION LIKE '%VANDALISM%'
    GROUP BY 
        CRIME_CODE_DESCRIPTION, TO_CHAR(Date_, 'MON-YY')
    ORDER BY 
        CRIME_CODE_DESCRIPTION, MIN(Date_)
    """)

    results = cursor.fetchall()

    df = pd.DataFrame(results, columns=['Crime', 'Month', 'Num_Crimes', 'Percent_Change'])
    df['Date'] = pd.to_datetime(df['Month'], format='%b-%y')
    df_pivot = df.pivot(index='Date', columns='Crime', values='Percent_Change')
    df_pivot.ffill(axis=0, inplace=True)
    df_pivot.reset_index(inplace=True)
    df_melted = pd.melt(df_pivot, id_vars='Date', value_vars=df['Crime'].unique(), value_name='Percent_Change', var_name='Crime')
    fig = px.line(df_melted, x='Date', y='Percent_Change', color='Crime', title='Crime Type Development Over Time')

    print(fig.data[0])
    fig_data = fig.to_html(full_html=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # fig.show()

    return render_template("queryone.html", graphJSON=graphJSON)

###############################################################################################################################
# Query 2:  How has the number of victims between the ages of 18-49 affected by crimes of theft and COVID-19 developed in 2020?
@app_blueprint.route('/querytwo')
def querytwo():
    # create a cursor object
    cursor = connection.cursor()
    cursor.execute("""
    SELECT 
        GONGBINGWONG.Crime.Date_,
        COUNT(*) AS Value,
        'Theft Victims' AS Category
    FROM 
        GONGBINGWONG.Crime
        JOIN GONGBINGWONG.Victim ON GONGBINGWONG.Crime.Crime_ID = GONGBINGWONG.Victim.Victim_Of
    WHERE 
        GONGBINGWONG.Victim.Age BETWEEN 18 AND 49 AND 
        GONGBINGWONG.Crime.Crime_Code_Description LIKE '%THEFT%' AND 
        GONGBINGWONG.Crime.Date_ >= TO_DATE('2019-01-01', 'YYYY-MM-DD') AND 
        GONGBINGWONG.Crime.Date_ <= TO_DATE('2022-12-31', 'YYYY-MM-DD') 
    GROUP BY 
        GONGBINGWONG.Crime.Date_
    
    UNION ALL

    SELECT 
        Case_Date,
        COUNT(*) AS Value,
        'COVID-19 Patients' AS Category
    FROM 
        COVID_19 JOIN Patient ON Case_ID = Infected_Case
    WHERE 
        Age_Group = '18 to 49 years' 
        AND Case_Date >= TO_DATE('2020-01-01', 'YYYY-MM-DD')  
        AND Case_Date <= TO_DATE('2022-12-31', 'YYYY-MM-DD') 
    GROUP BY 
        Case_Date""")
    
    # Fetch all the rows and store them in a list
    result = cursor.fetchall()

    # Create a Pandas DataFrame from the rows
    df = pd.DataFrame(result, columns=['Date', 'Value', 'Category'])

    # Pivot the DataFrame to create the data for the chart
    df_pivot = df.pivot(index='Date', columns='Category', values='Value')

    # Fill in missing values using forward-fill
    df_pivot = df_pivot.ffill(axis=0, inplace=True)

    # Reset the index so that the Date column becomes a regular column
    df_pivot.reset_index(inplace=True)

    # Create the chart using Plotly Express
    fig = px.line(df_pivot, x='Date', y=['Theft Victims', 'COVID-19 Patients'])

    # Get the Plotly JSON data and HTML for embedding the chart
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    fig_data = fig.to_html(full_html=False)

    return render_template("querytwo.html", graphJSON=graphJSON)

    # # execute the first query and save the results
    # query1 = """SELECT GONGBINGWONG.Crime.Date_, COUNT(*) AS num_victims 
    #         FROM GONGBINGWONG.Crime 
    #         JOIN GONGBINGWONG.Victim 
    #         ON GONGBINGWONG.Crime.Crime_ID = GONGBINGWONG.Victim.Victim_Of 
    #         WHERE GONGBINGWONG.Victim.Age BETWEEN 18 AND 49 
    #         AND GONGBINGWONG.Crime.Crime_Code_Description LIKE '%THEFT%' 
    #         AND GONGBINGWONG.Crime.Date_ >= TO_DATE('2019-01-01', 'YYYY-MM-DD') 
    #         AND GONGBINGWONG.Crime.Date_ <= TO_DATE('2022-12-31', 'YYYY-MM-DD') 
    #         GROUP BY GONGBINGWONG.Crime.Date_ 
    #         ORDER BY GONGBINGWONG.Crime.Date_ ASC"""
    # cursor.execute(query1)
    # result1 = cursor.fetchall()

    # # execute the second query and save the results
    # query2 = """SELECT Case_Date, COUNT(*) AS num_patients 
    #         FROM COVID_19 
    #         JOIN Patient 
    #         ON Case_ID = Infected_Case 
    #         WHERE Age_Group = '18 to 49 years' 
    #         AND Case_Date >= TO_DATE('2020-01-01', 'YYYY-MM-DD') 
    #         AND Case_Date <= TO_DATE('2022-12-31', 'YYYY-MM-DD') 
    #         GROUP BY Case_Date 
    #         ORDER BY Case_Date ASC"""
    # cursor.execute(query2)
    # result2 = cursor.fetchall()

    # # merge the results
    # merged_results = []
    # for i in range(len(result1)):
    #     merged_results.append([result1[i][0], result1[i][1], result2[i][1]])

    # # convert the merged results into a pandas data frame
    # df = pd.DataFrame(merged_results, columns=["Date", "Theft Victims", "COVID-19 Patients"])

    # # create a pivot table for the data frame
    # df_pivot = df.pivot_table(values=["Theft Victims", "COVID-19 Patients"], index="Date")

    # # create a melted version of the pivot table
    # df_melted = df_pivot.reset_index().melt(id_vars=["Date"], value_vars=["Theft Victims", "COVID-19 Patients"], var_name="Victim Type", value_name="Number of Victims/Patients")

    # # create a subplots object with two traces
    # fig = make_subplots(rows=1, cols=2, subplot_titles=("Number of Theft Victims", "Number of COVID-19 Patients"))

    # # add traces to the subplots object
    # fig.add_trace(go.Scatter(x=df_pivot.index, y=df_pivot[("Theft Victims")], mode='lines', name='Theft Victims', yaxis='y1'), row=1, col=1)
    # fig.add_trace(go.Scatter(x=df_pivot.index, y=df_pivot[("COVID-19 Patients")], mode='lines', name='COVID-19 Patients', yaxis='y2'), row=1, col=2)

    # # update the layout of the subplots object
    # fig.update_layout(title="Number of Theft Victims and COVID-19 Patients",
    #               xaxis_title="Date",
    #               yaxis=dict(title="Number of Theft Victims", titlefont=dict(color="#1f77b4"), tickfont=dict(color="#1f77b4")),
    #               yaxis2=dict(title="Number of COVID-19 Patients", titlefont=dict(color="#1f77b4"), tickfont=dict(color="#1f77b4"), anchor="free", overlaying="y", side="right"))

    # # update the traces of the subplots object
    # fig.update_traces(hoverinfo='y+x')

    # # convert the subplots object to JSON
    # graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # # render the JSON in a template
    # return render_template("querytwo.html", graphJSON=graphJSON)


##############################################################################################################
# Query 3: How does a certain area differ from other areas in terms of all crimes committed from 2010 to 2022? 
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


#########################################################################################################
# Query 4: How do the COVID-19 cases relate to the number of indoor and outdoor crimes from 2020 to 2022?
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


##################################################################################################################
# Query 5: What is the ratio of Hispanics to Non-Hispanics who were hospitalized due to COVID-19 and Hispanics to 
# Non-Hispanics who experienced [insert crime] from 2020 to the present? Can trend patterns be detected? 
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





