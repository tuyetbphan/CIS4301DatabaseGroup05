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
@app_blueprint.route('/queryone', methods=['GET', 'POST'])
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

    cursor = connection.cursor()
    cursor.execute("""
        SELECT 
    TRUNC(Date_, 'MM') AS Case_Date,
    COUNT(*) AS Value,
    'Theft Victims' AS Category,
    CASE
        WHEN Age BETWEEN 0 AND 17 THEN '0 - 17 years'
        WHEN Age BETWEEN 18 AND 49 THEN '18 to 49 years'
        WHEN Age BETWEEN 50 AND 64 THEN '50 to 64 years'
        WHEN Age > 64 THEN '65+ years'
        WHEN Age IS null THEN 'missing'
        END AS Age_Group
FROM 
    GONGBINGWONG.Crime
JOIN 
    GONGBINGWONG.Victim 
ON 
    GONGBINGWONG.Crime.Crime_ID = GONGBINGWONG.Victim.Victim_Of
WHERE 
    Crime_Code_Description LIKE '%THEFT%' AND 
    Date_ >= TO_DATE('2010-01-10', 'YYYY-MM-DD') AND 
    Date_ <= TO_DATE('2023-03-27', 'YYYY-MM-DD') 
GROUP BY 
    TRUNC(Date_, 'MM'), 
    CASE
        WHEN Age BETWEEN 0 AND 17 THEN '0 - 17 years'
        WHEN Age BETWEEN 18 AND 49 THEN '18 to 49 years'
        WHEN Age BETWEEN 50 AND 64 THEN '50 to 64 years'
        WHEN Age > 64 THEN '65+ years'
        WHEN Age IS null THEN 'missing'
        END

    UNION ALL

    SELECT 
        TRUNC(Case_Date, 'MM') AS Case_Date,
         COUNT(*) AS Value,
        'COVID-19 Patients' AS Category,
        Age_Group
       
    FROM 
        TPHAN1.COVID_19 
    JOIN 
    TPHAN1.Patient 
    ON 
    Case_ID = Infected_Case
    WHERE 
        Case_Date >= TO_DATE('2010-01-10', 'YYYY-MM-DD')  
        AND Case_Date <= TO_DATE('2023-03-27', 'YYYY-MM-DD')
        AND CURRENT_STATUS = 'Laboratory-confirmed case'
    GROUP BY 
        Case_Date, Age_Group
    """)
    
    result = cursor.fetchall()
    # df = pd.DataFrame(result, columns=['Date', 'Number of People', 'Category', 'Age Group'])
    df = pd.DataFrame(result, columns=['TRUNC(Date_, \'MM\')', 'Number of People', 'Category', 'Age_Group'])
    df['Age_Group'] = df['Age_Group'].astype('category')

    # Pivot the DataFrame to create separate columns for theft victims and COVID-19 patients
    # df_pivot = df.pivot(index='Case_Date', columns=['Category', 'Age_Group'], values='Value')
    df_pivot = df.pivot(index='TRUNC(Date_, \'MM\')', columns=['Category', 'Age_Group'], values='Number of People')
    print(df_pivot)
    # Create a line plot using Plotly Express
    fig = px.line(df_pivot, x=df_pivot.index, y=['Category', 'Age_Group'], title='Theft Victims and COVID-19 Patients')
    fig.update_layout(xaxis_title='Case Date', yaxis_title='Value')

    # Create a dropdown menu for selecting age groups
    age_groups = df['Age_Group'].unique().tolist()
    buttons = []
    for age_group in age_groups:
        buttons.append(dict(method='update', label=age_group, args=[{'visible': [False]*len(df_pivot.columns)},
                                                                {'title': f'Theft Victims and COVID-19 Patients ({age_group})'},
                                                                {'yaxis.title': f'Value ({age_group})'},
                                                                {'visible': [True if col.endswith(age_group) else False for col in df_pivot.columns]}]))

        updatemenus = [{'buttons': buttons,
                'direction': 'down',
                'showactive': True,
                'x': 0.1,
                'y': 1.1}]

        fig.update_layout(updatemenus=updatemenus)

    # Convert the plot to a JSON string for rendering in the web application
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("querytwo.html", graphJSON=graphJSON)


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

@app_blueprint.route('/queryfive', methods=['GET', 'POST'])
def queryfive():
    cursor = connection.cursor()
    cursor.execute("""
    SELECT 
        TO_CHAR(Date_, 'MON-YY') as month,
        Crime_Code_Description,
        SUM(CASE WHEN Descent = 'B' THEN 1 ELSE 0 END) / COUNT(*) AS Black,
        SUM(CASE WHEN Descent = 'W' THEN 1 ELSE 0 END) / COUNT(*) AS White,
        SUM(CASE WHEN Descent = 'I' THEN 1 ELSE 0 END) / COUNT(*) AS American_Indian,
        SUM(CASE WHEN Descent = 'C' THEN 1 ELSE 0 END) / COUNT(*) AS Chinese,
        SUM(CASE WHEN Descent = 'D' THEN 1 ELSE 0 END) / COUNT(*) AS Cambodian,
        SUM(CASE WHEN Descent = 'F' THEN 1 ELSE 0 END) / COUNT(*) AS Filipino,
        SUM(CASE WHEN Descent = 'J' THEN 1 ELSE 0 END) / COUNT(*) AS Japanese,
        SUM(CASE WHEN Descent = 'K' THEN 1 ELSE 0 END) / COUNT(*) AS Korean,
        SUM(CASE WHEN Descent = 'L' THEN 1 ELSE 0 END) / COUNT(*) AS Laotian,
        SUM(CASE WHEN Descent = 'V' THEN 1 ELSE 0 END) / COUNT(*) AS Vietnamese
    FROM 
        GONGBINGWONG.Crime
        JOIN GONGBINGWONG.Victim ON 
        GONGBINGWONG.Crime.Crime_ID = GONGBINGWONG.Victim.Victim_Of
    WHERE 
        Date_ >= TO_DATE('01-JAN-10', 'DD-MON-YY') AND 
        Date_ <= TO_DATE('01-DEC-22', 'DD-MON-YY') AND 
        GONGBINGWONG.Crime.Crime_Code_Description LIKE '%ASSAULT%'
    GROUP BY 
        Crime_Code_Description, TO_CHAR(Date_, 'MON-YY') 
    ORDER BY 
        MIN(Date_)
    """)


    query_results = cursor.fetchall()

    df = pd.DataFrame(query_results, columns=['Month', 'Crime_Code_Description', 'Black', 'White', 'American_Indian/Alaskan Native', 'Chinese', 'Cambodian', 'Filipino', 'Japanese', 'Korean', 'Laotian', 'Vietnamese'])

    # Create a plot for each crime code description
    crime_codes = df['Crime_Code_Description'].unique()

    if request.method == 'POST':
        selected_code = request.form.get('crime_code')
    else:
        selected_code = crime_codes[0]

    df_code = df[df['Crime_Code_Description'] == selected_code]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Black'], name='Black'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['White'], name='White'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['American_Indian/Alaskan Native'], name='American_Indian/Alaskan Native'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Chinese'], name='Chinese'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Cambodian'], name='Cambodian'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Filipino'], name='Filipino'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Japanese'], name='Japanese'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Korean'], name='Korean'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Laotian'], name='Laotian'))
    fig.add_trace(go.Scatter(x=df_code['Month'], y=df_code['Vietnamese'], name='Vietnamese'))
    fig.update_yaxes(title_text='Percentage of Victims')
    fig.update_xaxes(title_text='Month')
   

    fig.update_layout(height=1000, width=1200, title_text='Crime by Demographics')

    if len(fig.data) > 0:
        print(fig.data[0])
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template("queryfive.html", graphJSON=graphJSON, crime_codes=crime_codes)
    else:
        return "No data available for the specified time period and crime codes."


@app_blueprint.route('/records', methods=['GET', 'POST'])
def records():
    if request.method == 'POST':
        cursor = connection.cursor()
        cursor.execute("""SELECT COUNT(*) FROM GONGBINGWONG.CRIME""")
        crime_results = cursor.fetchall()

        cursor.execute("""SELECT COUNT(*) FROM GONGBINGWONG.Victim""")
        victim_results = cursor.fetchall()

        cursor.execute("""SELECT COUNT(*) FROM TPHAN1.Patient""")
        patient_results = cursor.fetchall()

        cursor.execute("""SELECT COUNT(*) FROM TPHAN1.COVID_19""")
        covid19_results = cursor.fetchall()

        cursor.execute("""
        SELECT SUM("COUNT(*)") AS TOTAL_SUM
        FROM (
            SELECT COUNT(*) FROM GONGBINGWONG.CRIME UNION ALL
            SELECT COUNT(*) FROM GONGBINGWONG.Victim UNION ALL
            SELECT COUNT(*) FROM TPHAN1.Patient UNION ALL
            SELECT COUNT(*) FROM TPHAN1.COVID_19
        ) COMBINED_TABLE
        """)
        total_results = cursor.fetchall()

        records = {
            'crime': crime_results[0][0],
            'victim': victim_results[0][0],
            'patient': patient_results[0][0],
            'covid19': covid19_results[0][0],
            'total': total_results[0][0]
        }
        return render_template('records.html', records=records)
    else:
        return render_template('records.html')