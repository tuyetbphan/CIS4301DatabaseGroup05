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
    print(df_pivot)
    df_pivot.ffill(axis=0, inplace=True)
    df_pivot.reset_index(inplace=True)
    df_melted = pd.melt(df_pivot, id_vars='Date', value_vars=df['Crime'].unique(), value_name='Percent_Change', var_name='Crime')
    fig = px.line(df_melted, x='Date', y='Percent_Change', color='Crime', title='Crime Type Development Over Time')

    print(fig.data[0])
    fig_data = fig.to_html(full_html=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    # fig.show()

    return render_template("queryone.html", graphJSON=graphJSON)

############################################################################################################################################################
# Query 2:  How has the number of victims between the ages of 18-49 affected by crimes of theft and COVID-19 developed in 2020? And the following two years?
@app_blueprint.route('/querytwo')
def querytwo():
    # create a cursor object
    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
        TRUNC(Date_, 'MM') AS Month_,
        COUNT(*) AS Value,
        'Theft Victims' AS Category
    FROM 
        GONGBINGWONG.Crime
        JOIN GONGBINGWONG.Victim ON GONGBINGWONG.Crime.Crime_ID = GONGBINGWONG.Victim.Victim_Of
    WHERE 
        Age BETWEEN 18 AND 49 AND 
        Crime_Code_Description LIKE '%THEFT%' AND 
        Date_ >= TO_DATE('2020-01-01', 'YYYY-MM-DD') AND 
        Date_ <= TO_DATE('2022-12-31', 'YYYY-MM-DD') 
    GROUP BY 
        TRUNC(Date_, 'MM')
    
    UNION ALL

    SELECT 
        Case_Date,
        COUNT(*) AS Value,
        'COVID-19 Patients' AS Category
    FROM 
        TPHAN1.COVID_19 JOIN TPHAN1.Patient ON Case_ID = Infected_Case
    WHERE 
        Age_Group = '18 to 49 years' 
        AND Case_Date >= TO_DATE('2020-01-01', 'YYYY-MM-DD')  
        AND Case_Date <= TO_DATE('2022-12-31', 'YYYY-MM-DD')
        AND CURRENT_STATUS = 'Laboratory-confirmed case'
    GROUP BY 
        Case_Date
    """)
    
    result = cursor.fetchall()

    df = pd.DataFrame(result, columns=['Date', 'Value', 'Category'])
    print(df)
    df_pivot = df.pivot(index='Date', columns='Category', values='Value')
    df_pivot = df_pivot.ffill(axis=0)
    df_pivot.reset_index(inplace=True)
    print(df_pivot)
    df_melted = pd.melt(df_pivot, id_vars='Date', value_vars=df['Category'].unique(), value_name='Number of Affected People', var_name='Category')
    fig = px.line(df_melted, x='Date', y='Number of Affected People', color='Category')
    print(fig.data[0])
    fig_data = fig.to_html(full_html=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("querytwo.html", graphJSON=graphJSON)


    
    # result = cursor.fetchall()

    # df = pd.DataFrame(result, columns=['Date', 'Value', 'Category'])
    # df_pivot = df.pivot(index='Date', columns='Category', values='Value')
    # df_pivot = df_pivot.ffill(axis=0, inplace=True)
    # if df_pivot is not None:
    #     df_pivot.reset_index(inplace=True)
    #     fig = px.line(df_pivot, x='Date', y=['Theft Victims', 'COVID-19 Patients'])
    #     print(fig.data[0])
    #     fig_data = fig.to_html(full_html=False)
    #     graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # return render_template("querytwo.html", graphJSON=graphJSON)
    # Reset the index so that the Date column becomes a regular column
    # df_pivot.reset_index(inplace=True)
    # df_pivot = df_pivot.reset_index()

    # if df_pivot is not None:
    #     df_pivot.reset_index(inplace=True)
    # fig = px.line(df_pivot, x='Date', y=['Theft Victims', 'COVID-19 Patients'])
    # print(fig.data[0])
    # fig_data = fig.to_html(full_html=False)
    # graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # return render_template("querytwo.html", graphJSON=graphJSON)


    


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

    #Not completely finished.
    cursor = connection.cursor()
    cursor.execute("""
SELECT
    r.year,
    r.month,
    r.residential_crime_count,
    r.non_residential_crime_count,
    COALESCE(d.total_cases, 0) as total_covid_19_cases
FROM
(SELECT 
    EXTRACT(YEAR FROM Date_) AS year, 
    EXTRACT(MONTH FROM Date_) AS month, 
    SUM(CASE WHEN c.PREMISE_CODE_DESCRIPTION IN ('DRIVEWAY', 'TOOL SHED*', 'TRANSITIONAL HOUSING/HALFWAY HOUSE', 'TRANSIENT ENCAMPMENT', 'PROJECT/TENEMENT/PUBLIC HOUSING', 
    'PATIO*', 'BALCONY*', 'OTHER RESIDENCE', 'YARD (RESIDENTIAL/BUSINESS)', 'TV/RADIO/APPLIANCE', 'WEBSITE', 'MISSIONS/SHELTERS', 'NURSING/CONVALESCENT/RETIREMENT HOME', 
    'STORAGE SHED', 'GROUP HOME', 'FOSTER HOME BOYS OR GIRLS*', 'TRASH CAN/TRASH DUMPSTER', 'SINGLE FAMILY DWELLING', 'GARAGE/CARPORT', 'PARKING UNDERGROUND/BUILDING', 
    'CONDOMINIUM/TOWNHOUSE', 'SINGLE RESIDENCE OCCUPANCY (SRO''S) LOCATIONS', 'ABANDONED BUILDING ABANDONED HOUSE', 'HOSPITAL', 'STAIRWELL*', 'PORCH, RESIDENTIAL', 'STREET', 
    'FRAT HOUSE/SORORITY/DORMITORY', 'APARTMENT/CONDO COMMON LAUNDRY ROOM', 'MULTI-UNIT DWELLING (APARTMENT, DUPLEX, ETC)', 'MOBILE HOME/TRAILERS/CONSTRUCTION TRAILERS/RV''S/MOTORHOME') THEN 1 ELSE 0 END) AS residential_crime_count,
    SUM(CASE WHEN c.PREMISE_CODE_DESCRIPTION NOT IN ('DRIVEWAY', 'TOOL SHED*', 'TRANSITIONAL HOUSING/HALFWAY HOUSE', 'TRANSIENT ENCAMPMENT', 'PROJECT/TENEMENT/PUBLIC HOUSING', 
    'PATIO*', 'BALCONY*', 'OTHER RESIDENCE', 'YARD (RESIDENTIAL/BUSINESS)', 'TV/RADIO/APPLIANCE', 'WEBSITE', 'MISSIONS/SHELTERS', 'NURSING/CONVALESCENT/RETIREMENT HOME', 
    'STORAGE SHED', 'GROUP HOME', 'FOSTER HOME BOYS OR GIRLS*', 'TRASH CAN/TRASH DUMPSTER', 'SINGLE FAMILY DWELLING', 'GARAGE/CARPORT', 'PARKING UNDERGROUND/BUILDING', 
    'CONDOMINIUM/TOWNHOUSE', 'SINGLE RESIDENCE OCCUPANCY (SRO''S) LOCATIONS', 'ABANDONED BUILDING ABANDONED HOUSE', 'HOSPITAL', 'STAIRWELL*', 'PORCH, RESIDENTIAL', 'STREET', 
    'FRAT HOUSE/SORORITY/DORMITORY', 'APARTMENT/CONDO COMMON LAUNDRY ROOM', 'MULTI-UNIT DWELLING (APARTMENT, DUPLEX, ETC)', 'MOBILE HOME/TRAILERS/CONSTRUCTION TRAILERS/RV''S/MOTORHOME') THEN 1 ELSE 0 END) AS non_residential_crime_count
FROM 
    GONGBINGWONG.Crime c 
WHERE 
     c.Date_ >= TO_DATE('01-JAN-10', 'DD-MON-YY') AND c.Date_ <= TO_DATE('27-MAR-23', 'DD-MON-YY')
GROUP BY 
    EXTRACT(YEAR FROM c.Date_), 
    EXTRACT(MONTH FROM c.Date_)) r
LEFT JOIN
(SELECT 
    EXTRACT(YEAR FROM b.case_date) AS year, 
    EXTRACT(MONTH FROM b.case_date) AS month,
    COUNT(*) AS total_cases
FROM 
    TPHAN1.COVID_19 b
WHERE 
    b.case_date >= TO_DATE('01-JAN-20', 'DD-MON-YY') AND b.case_date <= TO_DATE('01-FEB-23', 'DD-MON-YY')
GROUP BY 
    EXTRACT(YEAR FROM b.case_date), 
    EXTRACT(MONTH FROM b.case_date)) d
on r.year = d.year and r.month = d.month
ORDER BY
    year, month
    """)

    query_results = cursor.fetchall()
    df = pd.DataFrame(query_results, columns=['Year', 'Month', 'Residential_Crime_Count', 'Non_Residential_Crime_Count', 'Total_COVID_19_Cases'])
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['Month'].astype(str), format='%Y-%m')
    df = df.drop(['Year', 'Month'], axis=1)
    df_melted = pd.melt(df, id_vars=['Date', 'Total_COVID_19_Cases'], var_name='Crime_Type', value_name='Crime_Count')
    fig = px.line(df_melted, x='Date', y='Crime_Count', color='Crime_Type', title='Total Crimes and COVID-19 Cases by Month')
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Total_COVID_19_Cases'], name='Total COVID-19 Cases', yaxis='y2'))
    fig.update_layout(yaxis=dict(title='Crime Count', side='left'), yaxis2=dict(title='Total COVID-19 Cases', overlaying='y', side='right'),
                    legend=dict(x=1.125, y=1))
    print(fig.data[0])
    fig_data = fig.to_html(full_html=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template("queryfour.html", graphJSON=graphJSON)







##################################################################################################################
# Query 5: What is the ratio of Hispanics to Non-Hispanics who were hospitalized due to COVID-19 and Hispanics to 
# Non-Hispanics who experienced [insert crime] from 2020 to the present? Can trend patterns be detected? 
@app_blueprint.route('/queryfive')
def queryfive():
    cursor = connection.cursor()
    # cursor.execute("""
    # select x.year, x.month, x."Hospitalized Hispanic", y."Hospitalized Non-Hispanic" 
    # from 
    # (
    #     select EXTRACT(YEAR FROM case_Date) AS year, EXTRACT(MONTH FROM case_Date) AS month, count(*) as "Hospitalized Hispanic"     
    #     from tphan1.covid_19 join tphan1.patient on tphan1.covid_19.case_id = tphan1.patient.infected_case 
    #     where case_Date >= TO_DATE('01-JAN-10', 'DD-MON-YY') AND case_Date <= TO_DATE('27-MAR-23', 'DD-MON-YY') and tphan1.covid_19.hospitalized = 'Yes' and tphan1.patient.ethnicity = 'Hispanic/Latino'
    #     GROUP BY EXTRACT(YEAR FROM case_Date), EXTRACT(MONTH FROM case_Date)
    # ) x 
    # inner join 
    # (
    #     select EXTRACT(YEAR FROM case_Date) AS year, EXTRACT(MONTH FROM case_Date) AS month, count(*) as "Hospitalized Non-Hispanic" 
    #     from tphan1.covid_19 join tphan1.patient on tphan1.covid_19.case_id = tphan1.patient.infected_case 
    #     where case_Date >= TO_DATE('01-JAN-10', 'DD-MON-YY') AND case_Date <= TO_DATE('27-MAR-23', 'DD-MON-YY') and tphan1.covid_19.hospitalized = 'Yes' and tphan1.patient.ethnicity = 'Non-Hispanic/Latino'
    #     GROUP BY EXTRACT(YEAR FROM case_Date), EXTRACT(MONTH FROM case_Date)
    # ) y on x.year = y.year and x.month = y.month
    # order by x.year, x.month
    # """)
    cursor.execute("""
        WITH covid_data AS (
    SELECT
        EXTRACT(YEAR FROM case_Date) AS year,
        EXTRACT(MONTH FROM case_Date) AS month,
        COUNT(CASE WHEN tphan1.patient.ethnicity = 'Hispanic/Latino' THEN 1 END) AS "Hospitalized Hispanic",
        COUNT(CASE WHEN tphan1.patient.ethnicity = 'Non-Hispanic/Latino' THEN 1 END) AS "Hospitalized Non-Hispanic"
    FROM 
        tphan1.covid_19 JOIN tphan1.patient ON 
        tphan1.covid_19.case_id = tphan1.patient.infected_case
    WHERE 
        case_Date >= TO_DATE('01-JAN-10', 'DD-MON-YY') AND 
        case_Date <= TO_DATE('27-MAR-23', 'DD-MON-YY') AND 
        tphan1.covid_19.hospitalized = 'Yes'
    GROUP BY 
        EXTRACT(YEAR FROM case_Date), 
        EXTRACT(MONTH FROM case_Date)
    ),
    crime_data AS (
    SELECT
        EXTRACT(YEAR FROM date_) AS year,
        EXTRACT(MONTH FROM date_) AS month,
        COUNT(CASE WHEN descent = 'H' THEN 1 END) AS "Hispanic Victims",
        COUNT(CASE WHEN NOT descent = 'H' THEN 1 END) AS "Non-Hispanic Victims"
    FROM 
        gongbingwong.victim JOIN gongbingwong.crime ON 
        gongbingwong.victim.victim_of = gongbingwong.crime.crime_id
    WHERE 
        crime_code_description IN 
        (
        'RESISTING ARREST',
        'ARSON',
        'FALSE POLICE REPORT',
        'CRIMINAL THREATS - NO WEAPON DISPLAYED',
        'TRESPASSING',
        'DOCUMENT FORGERY / STOLEN FELONY',
        'FAILURE TO DISPERSE',
        'BATTERY POLICE (SIMPLE)',
        'ASSAULT WITH DEADLY WEAPON ON POLICE OFFICER',
        'INCITING A RIOT',
        'DISTURBING THE PEACE'
        )
    GROUP BY 
        EXTRACT(YEAR FROM date_), EXTRACT(MONTH FROM date_)
    )
    SELECT
        covid_data.year,
        covid_data.month,
        covid_data."Hospitalized Hispanic",
        covid_data."Hospitalized Non-Hispanic",
        crime_data."Hispanic Victims",
        crime_data."Non-Hispanic Victims"
    FROM 
        covid_data JOIN crime_data ON 
        covid_data.year = crime_data.year AND covid_data.month = crime_data.month
    ORDER BY covid_data.year, covid_data.month
    """)
    query_results = cursor.fetchall()

    # cursor.execute("""
    # SELECT x.year, x.month, x."Hispanic Victims", y."Non-Hispanic Victims"
    # FROM
    # (   
    #     SELECT  crime_code_description, EXTRACT(YEAR FROM date_) AS year, EXTRACT(MONTH FROM date_) AS month, COUNT(*) AS "Hispanic Victims"
    #     FROM gongbingwong.victim
    #     JOIN 
    #     gongbingwong.crime ON gongbingwong.victim.victim_of = gongbingwong.crime.crime_id
    #     WHERE descent = 'H'AND
    #     crime_code_description = 'RESISTING ARREST' OR
    #     crime_code_description = 'ARSON' OR
    #     crime_code_description = 'FALSE POLICE REPORT' OR
    #     crime_code_description = 'CRIMINAL THREATS - NO WEAPON DISPLAYED' OR
    #     crime_code_description = 'TRESPASSING' OR
    #     crime_code_description = 'DOCUMENT FORGERY / STOLEN FELONY' OR
    #     crime_code_description = 'FAILURE TO DISPERSE' OR
    #     crime_code_description = 'BATTERY POLICE (SIMPLE)' OR
    #     crime_code_description = 'ASSAULT WITH DEADLY WEAPON ON POLICE OFFICER' OR
    #     crime_code_description = 'INCITING A RIOT' OR
    #     crime_code_description = 'DISTURBING THE PEACE' 
    #     GROUP BY crime_code_description, EXTRACT(YEAR FROM date_), EXTRACT(MONTH FROM date_)
    # ) x
    # INNER JOIN
    # (
    #     SELECT  crime_code_description, EXTRACT(YEAR FROM date_) AS year, EXTRACT(MONTH FROM date_) AS month, COUNT(*) AS "Non-Hispanic Victims"
    #     FROM gongbingwong.victim
    #     JOIN 
    #     gongbingwong.crime ON gongbingwong.victim.victim_of = gongbingwong.crime.crime_id
    #     WHERE NOT descent = 'H' AND
    #     crime_code_description = 'RESISTING ARREST' OR
    #     crime_code_description = 'ARSON' OR
    #     crime_code_description = 'FALSE POLICE REPORT' OR
    #     crime_code_description = 'CRIMINAL THREATS - NO WEAPON DISPLAYED' OR
    #     crime_code_description = 'TRESPASSING' OR
    #     crime_code_description = 'DOCUMENT FORGERY / STOLEN FELONY' OR
    #     crime_code_description = 'FAILURE TO DISPERSE' OR
    #     crime_code_description = 'BATTERY POLICE (SIMPLE)' OR
    #     crime_code_description = 'ASSAULT WITH DEADLY WEAPON ON POLICE OFFICER' OR
    #     crime_code_description = 'INCITING A RIOT' OR
    #     crime_code_description = 'DISTURBING THE PEACE' 
    #     GROUP BY crime_code_description, EXTRACT(YEAR FROM date_), EXTRACT(MONTH FROM date_)
    # ) y ON x.year = y.year and x.month = y.month AND x.crime_code_description=y.crime_code_description
    # ORDER BY x.crime_code_description, x.year, x.month
    # """)
    # query_results2 = cursor.fetchall()

    df = pd.DataFrame(query_results, columns=['Year', 'Month', 'Hospitalized Hispanic', 'Hospitalized Non-Hispanic', 'Hispanic Victims', 'Non-Hispanic Victims'])

    df['Date'] = pd.to_datetime(df['Year'])
    df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
    # df_pivot = df.pivot_table(index='Date', values=['HospitalizedHispanic', 'HospitalizedNonHispanic'])
    # trace0 = go.Scatter(x=df_pivot.index, y=df_pivot.HospitalizedHispanic, mode='lines', name='Hospitalized Hispanics')
    # trace1 = go.Scatter(x=df_pivot.index, y=df_pivot.HospitalizedNonHispanic, mode='lines', name='Hospitalized Non-Hispanics')
    # data = [trace0, trace1]
    # layout = go.Layout(title='Information')
    # figure = go.Figure(data=data, layout=layout)
    # df_pivot.ffill(axis=0, inplace=True)
    # df_pivot.reset_index(inplace=True)
    # df_melted = pd.melt(df_pivot, id_vars='Date', value_vars=df['Hospitalized'].unique(), value_name='HospitalizedHispanic', var_name='Hospitalized')
    fig = px.line(df, x='Date', y=['Hospitalized Hispanic','Hospitalized Non-Hispanic', 'Hispanic Victims', 'Non-Hispanic Victims'], title='Ratio Between Affected Ethnicities')
    # fig = px.line(df, x='Date', y='Hospitalized Hispanic', title='Total Crimes by Month')
    # fig.add_scatter(x=df['Date'], y=df['Hospitalized Non-Hispanic'], mode='lines')

    print(fig.data[0])
    fig_data = fig.to_html(full_html=False)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template("queryfive.html", graphJSON=graphJSON)


    # SELECT x.year, x.month, x.crime_code_description, x."Hispanic Victims", y."Non-Hispanic Victims"
    # FROM
    # (
    #     SELECT  crime_code_description, EXTRACT(YEAR FROM date_) AS year, EXTRACT(MONTH FROM date_) AS month, COUNT(*) AS "Hispanic Victims"
    #     FROM gongbingwong.victim
    #     JOIN 
    #     gongbingwong.crime ON gongbingwong.victim.victim_of = gongbingwong.crime.crime_id
    #     WHERE descent = 'H'
    #     GROUP BY crime_code_description, EXTRACT(YEAR FROM date_), EXTRACT(MONTH FROM date_)
    # ) x
    # INNER JOIN
    # (
    #     SELECT  crime_code_description, EXTRACT(YEAR FROM date_) AS year, EXTRACT(MONTH FROM date_) AS month, COUNT(*) AS "Non-Hispanic Victims"
    #     FROM gongbingwong.victim
    #     JOIN 
    #     gongbingwong.crime ON gongbingwong.victim.victim_of = gongbingwong.crime.crime_id
    #     WHERE NOT descent = 'H'
    #     GROUP BY crime_code_description, EXTRACT(YEAR FROM date_), EXTRACT(MONTH FROM date_)
    # ) y ON x.year = y.year and x.month = y.month AND x.crime_code_description=y.crime_code_description
    # ORDER BY x.year, x.month



