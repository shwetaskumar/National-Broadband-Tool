import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from operator import itemgetter
import altair as alt
import xgboost as xgb
import branca
import requests
from joblib import load
import json
import numpy as np
from sklearn.cluster import KMeans
from openai import OpenAI
import os

st.set_page_config(layout="wide")

def get_bounds(df):
    bounds = df.geometry.apply(lambda x: x.bounds).tolist()
    minx, miny, maxx, maxy = min(bounds, key=itemgetter(0))[0], min(bounds, key=itemgetter(1))[1], max(bounds, key=itemgetter(2))[2], max(bounds, key=itemgetter(3))[3]
    return [[miny,minx], [maxy,maxx]]

@st.cache_resource
def get_df_lat_long(state_code):
    merged_data = pd.read_parquet(path="DATA/visual_data.parquet")
    merged_data['Income Score'] = merged_data['income_score']
    merged_data['Employment Score'] = merged_data['employment_score']
    merged_data['Education Score'] = merged_data['education_score']
    merged_data['Development Score'] = merged_data['development_score']
    state_pd = pd.read_csv("DATA/states.csv",dtype={'state':str,'lat':float,'lng':float,'name':str,'code':str})
    state_lat = state_pd[state_pd['code'] == state_code]['latitude'].values[0]
    state_long = state_pd[state_pd['code'] == state_code]['longitude'].values[0]
    
    filtered_data = merged_data[(merged_data['state_code'] == state_code)].copy(deep=True)
    county_data = filtered_data.drop(['Year','tract_code','cluster'],axis=1).groupby(['county_code','state_code','county_name','state_name']).mean().reset_index()
    # round popoulation to nearest 1000
    cols = ['Population', 'Male', 'Female', 'White', 'Black', 'Asian', 'Native', 'Pacific', 'Other', 'Multi-Race']
    for i in county_data[cols]:
        county_data[i] = county_data[i].apply(lambda x: round(x))
    county_data['county_code'] = county_data['county_code'].apply(lambda x: x[-3:])
    data_geo_tract = gpd.read_file('https://raw.githubusercontent.com/shwetaskumar/NBTShapes/main/SHAPES/tract/tl_2021_{}_tract.json'.format(state_code))
    data_geo_county = gpd.read_file('https://raw.githubusercontent.com/shwetaskumar/NBTShapes/main/SHAPES/county/tl_2021_{}_county.geojson'.format(state_code))
    merged_geo_tract = data_geo_tract.merge(filtered_data, right_on='tract_code', left_on='GEOID', how='left')
    merged_geo_county = data_geo_county.merge(county_data, right_on='county_code', left_on='COUNTYFP', how='left')
    
    income_model = xgb.Booster(model_file='MODELS/income_model_lag2.json')
    education_model = xgb.Booster(model_file='MODELS/education_model_lag2.json')
    employment_model = xgb.Booster(model_file='MODELS/employment_model_lag2.json')
    
    if state_code == '02':
            minx, miny, maxx, maxy = -179.231086, 51.175092, -140, 71.365162 # Alaska overlaps the international date line
            bounds = [[miny,minx], [maxy,maxx]]
    else:
        bounds = get_bounds(data_geo_county)
    return merged_geo_tract,merged_geo_county,[state_lat,state_long],bounds,income_model,education_model,employment_model,merged_data

def predict_data(df,income_model,education_model,employment_model):
    data_income = df[['Year', 'connections_above25', 'connections_below25', 'male_Population', 'female_Population', 'under25_Population', 'over25_Population', 'seniors_Population', 'veterans_Population', 'non_veterans_Population', 'disability_below65_Population', 'disability_above65_Population', 'total_ea_noSchooling%', 'total_ea_noDiploma%', 'total_ea_highschool%', 'total_ea_GED_alternate%', 'total_ea_associates%', 'total_ea_bachelors%', 'total_ea_masters%', 'total_ea_professional%', 'total_ea_doctorate%', 'belowPoverty%', 'total_employed%', 'total_unemployed%', 'total_value_household_less100k%', 'total_value_household_100k_1000k%', 'total_value_household_1000k+%', 'total_1939_2000%', 'total_2000_2014+%', 'internet_broadband%', 'internet_other%', 'no_Internet%']].rename(columns={'total_value_household_less100k%':'total_value_household_less100k%'})
    data_income = xgb.DMatrix(data_income)
    
    data_employment = df[['Year', 'connections_above25', 'connections_below25',
       'male_Population', 'female_Population', 'under25_Population',
       'over25_Population', 'seniors_Population', 'veterans_Population',
       'non_veterans_Population', 'disability_below65_Population',
       'disability_above65_Population', 'total_ea_noSchooling%',
       'total_ea_noDiploma%', 'total_ea_highschool%',
       'total_ea_GED_alternate%', 'total_ea_associates%',
       'total_ea_bachelors%', 'total_ea_masters%', 'total_ea_professional%',
       'total_ea_doctorate%', 'abovePoverty%', 'belowPoverty%',
       'total_unemployed%', 'total_value_household_less100k%',
       'total_value_household_100k_1000k%', 'total_value_household_1000k+%',
       'total_1939_2000%', 'total_2000_2014+%', 'internet_broadband%',
       'internet_other%', 'no_Internet%']].rename(columns={'total_value_household_less100k%':'total_value_household_less100k%'})
    data_employment = xgb.DMatrix(data_employment)
    
    data_education = df[['Year', 'connections_above25', 'connections_below25',
       'male_Population', 'female_Population', 'under25_Population',
       'over25_Population', 'seniors_Population', 'veterans_Population',
       'non_veterans_Population', 'disability_below65_Population',
       'disability_above65_Population', 'abovePoverty%', 'belowPoverty%',
       'total_employed%', 'total_unemployed%',
       'total_value_household_less100k%', 'total_value_household_100k_1000k%',
       'total_value_household_1000k+%', 'total_1939_2000%',
       'total_2000_2014+%', 'internet_broadband%', 'internet_other%',
       'no_Internet%']].rename(columns={'total_value_household_less100k%':'total_value_household_less100k%'})
    data_education = xgb.DMatrix(data_education)
    
    
    income_prediction = income_model.predict(data_income)[0]
    employment_prediction = employment_model.predict(data_employment)[0]
    education_prediction = education_model.predict(data_education)[0]
    
    return [income_prediction,employment_prediction,education_prediction]

def get_top_5(tract_code, clustered_df):
    score_columns = ['connections_above25', 'income_score', 'employment_score', 'education_score']
    
    # Get the current tract's scores
    current_tract_scores = clustered_df[clustered_df['tract_code'] == tract_code][score_columns].iloc[0]
    
    # Get the cluster label for the current tract
    cluster_label = clustered_df[clustered_df['tract_code'] == tract_code]['cluster'].values[0]
    
    # Filter the DataFrame for tracts in the same cluster
    same_cluster_df = clustered_df[clustered_df['cluster'] == cluster_label]
    
    # Compare each tract's scores to the current tract's scores and keep only those with higher scores in all categories
    better_tracts = same_cluster_df[(same_cluster_df[score_columns] > current_tract_scores).all(axis=1)]
    
    # If there are less than 5, return them all, otherwise return the top 5 based on 'connections_above25'
    if len(better_tracts) < 5:
        top_5_tracts = better_tracts
    else:
        top_5_tracts = better_tracts.nlargest(5, 'connections_above25')
    
    # Return the tract codes of the top 5 tracts
    return top_5_tracts[['tract_code', 'county_name', 'connections_above25', 'income_score', 'employment_score', 'education_score']]

def color_values(val):
    color = 'red' if val < 0 else 'green' if val > 0 else 'black'
    return f'color: {color}'          
    

def analyze_tract_investment(df1, df2):
    
    os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
    client = OpenAI()
    # Convert DataFrames to a JSON-like format for analysis
    data_for_analysis = {
        'current_tract_scores': df1.to_dict(orient='records'),
        'top_performing_tracts': df2.to_dict(orient='records')
    }
    
    # Convert the data to a string that will be used as a prompt for the API
    prompt = (
        f"{json.dumps(data_for_analysis)}"
    )
    
    # Send the data to the OpenAI API
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {'role':'system','content':'You are an analyst with the US Government. You have been given the task of analyzing a census tract for potential broadband investment. You have been provided with the current tract scores and the top performing tracts in similar demographic clusters with higher socio-economic scores. You have to analyze if the current tract is a suitable candidate for potential broadband investment. Suggest only your recommendation and DO NOT PROVIDE YOUR WORKINGS. BE CONCISE.'},
            {'role':'user','content':prompt}
        ],
        max_tokens=256
    )
    
    # Get the analysis from the response
    analysis = response.choices[0].message.content
    
    return analysis

flag_predict = 0


if 'selected_state' and 'selected_state_code' not in st.session_state:
    st.title("No State Selected")
else:
    state = st.session_state['selected_state']
    state_code = st.session_state['selected_state_code']
    merged_geo_tract,merged_geo_county,lat_long,bounds,income_model,education_model,employment_model,main_data = get_df_lat_long(state_code)
    # clustered_df = get_cluster(merged_geo)
    col1,col2,col3 = st.columns([2,4,4])
    # county = None
    # tract = None
    
    
    
    with col1:
        st.title(f"{state.upper()}")
        county = st.selectbox("Select a County",options=merged_geo_county['county_name'].unique(),index=None,placeholder = "Select a County")
        if county!=None:
            tract = st.selectbox("Select a Census Tract",options=merged_geo_tract[merged_geo_tract['county_name']==county]['tract_code'].unique(),index=None,placeholder = "Select a Census Tract")
        else:
            # tract = st.selectbox("Select a Census Tract",options=merged_geo['tract_code'].unique(),index=None,placeholder = "Select a Census Tract")
            tract = None

        if county!=None and tract!=None:
            st.markdown(":red[Check the potential growth in Income, Employment and Education Score by increasing the Digital Index by x%.]")
            delta = st.slider("Select a % Increase in the Digital Index",min_value=0,max_value=100,value=20,step=5)
            tract_code = tract.split(" - ")[0]
            tract_data = merged_geo_tract[(merged_geo_tract['tract_code'].str.contains(tract_code)) & (merged_geo_tract['county_name'].str.contains(county))].iloc[[0]].reset_index(drop=True)
            # tract_data.iloc[0].index = [0]
            if (tract_data['internet_broadband%'].values[0]  + (delta/100)) > 1:
                tract_data['internet_broadband%'] = 1
            else:
                tract_data['internet_broadband%'] = tract_data['internet_broadband%'] + (delta/100)
            if (tract_data['no_Internet%'].values[0] < (delta/100)):
                tract_data['no_Internet%'] = 0
                tract_data['internet_other%'] = tract_data['internet_other%'] + (tract_data['no_Internet%'] - (delta/100))
            else:
                tract_data['no_Internet%'] = tract_data['no_Internet%'] - (delta/100)
            if (tract_data['connections_below25'].values[0] < (delta/100)):
                tract_data['connections_below25'] = 0
                tract_data['connections_above25'] = 1
            else:
                tract_data['connections_below25'] = tract_data['connections_below25'] - (delta/100)
                tract_data['connections_above25'] = tract_data['connections_above25'] + (delta/100)
            tract_data['Year'] = tract_data['Year'] + 1
            if st.button("Predict"):
                flag_predict = 1
            else:
                flag_predict = 0
    
    with col2:
        if county!=None and tract!=None and flag_predict == 1:
            
                prediction = predict_data(tract_data,income_model,education_model,employment_model)
                results = pd.DataFrame({"Current Score":[tract_data['Income Score'].values[0],tract_data['Employment Score'].values[0],tract_data['Education Score'].values[0]],"Predicted Score":[prediction[0],prediction[1],prediction[2]],"Growth/Drop %":[(prediction[0] - tract_data['Income Score'].values[0])*100,(prediction[1] - tract_data['Employment Score'].values[0])*100,(prediction[2] - tract_data['Education Score'].values[0])*100]},index=['Income','Employment','Education'])
                col_list = ['Current Score', 'Predicted Score', 'Growth/Drop %']
                for col in col_list:
                    if col == 'Growth/Drop %':
                        results[col] = results[col].apply(lambda x: round(x,2))
                    else:
                        results[col] = results[col].apply(lambda x: round(x*100,2))
                
                st.markdown(":maroon[The predicted growth in Income, Employment and Education Score over next 2 years is shown below.]")
                st.dataframe(results.style.applymap(color_values, subset=['Growth/Drop %'])
                             .format({'Current Score': "{:.2f}", 'Predicted Score': "{:.2f}", "Growth/Drop %": "{:.2f}%"})
                             .set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='td', props=[('text-align', 'center')])]), use_container_width=True)
                
                top_5_clusters = get_top_5(tract_code, main_data)
                # Multiply by 100 to get percentages except for 'connections_above25' and 'tract_code'
                top_5_clusters[['income_score', 'employment_score', 'education_score']] = top_5_clusters[['income_score', 'employment_score', 'education_score']] * 100
                st.markdown(":maroon[In evaluating a census tract for broadband investment, we'll benchmark it against the top five demographically similar tracts with higher socio-economic scores to gauge potential gains.]")
                st.dataframe(top_5_clusters.sort_values(['connections_above25'],ascending=False).set_index('tract_code').round(2).head())
                
                analysis_result = analyze_tract_investment(results, top_5_clusters)
                st.write(analysis_result)
                
                url = "https://chat.openai.com/g/g-8v4Z093ln-national-broadband-gpt"
                
                st.markdown(f'<a href="{url}" target="_blank"><button style="color: black; background-color: #FF4B4B; padding: 10px 24px; border-radius: 8px; border: none; cursor: pointer; text-align: center; text-decoration: none; display: inline-block; font-size: 16px;">Chat with NBT.AI to build your grant proposal!</button></a>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('The Digital Index quantifies broadband access by the share of connections above 25 Mbps on a scale from 0 to 1; areas with values near 0, **shown in darker red, are priority zones** for network enhancements due to their limited high-speed connectivity.')
        map = folium.Map(location=lat_long,zoom_start=6,scrollWheelZoom=False, tiles='cartodbpositron')
        fg = folium.FeatureGroup(name="State bounds")
        if county==None:
            colormap = branca.colormap.LinearColormap(
                vmin=0,
                vmax=1,
                colors=["#540B0E", "#9E2A2B", "#E09F3E", "#FFF3B0", "#335c67"],
                caption="Digital Index (%)",
            )
            
            tooltip = folium.GeoJsonTooltip(
                fields=["NAME", "Population", "connections_above25"],
                aliases=["County:", "Population:   ", "Digital Index:"],
                localize=True,
                sticky=False,
                labels=True,
                style="""
                    background-color: #F0EFEF;
                    border: 1px solid grey;
                    border-radius: 1px;
                    box-shadow: 1px;
                """,
                max_width=800,
            )
            g = folium.GeoJson(
                merged_geo_county,
                style_function=lambda x: {
                    "fillColor": colormap(x["properties"]["connections_above25"])
                    if x["properties"]["connections_above25"] is not None
                    else "transparent",
                    "color": "black",
                    "fillOpacity": 0.6,
                    "weight": 0.3,
                },
                tooltip=tooltip,
            ).add_to(map)
            # Iterate over the GeoDataFrame to place county names
            for _, row in merged_geo_county.iterrows():
                # Extract the centroid of the county's boundary for the marker's location
                centroid = row['geometry'].centroid
                folium.Marker(
                    [centroid.y, centroid.x],  # y is latitude and x is longitude
                    popup=row['NAME'],  # The county name will appear in a popup on click
                    icon=folium.DivIcon(html=f"""<div style="font-size: 0.8rem">{row['NAME']}</div>""")  # Or use DivIcon for a label
                ).add_to(map)
            map.add_child(colormap)
        else:
            bounds = get_bounds(merged_geo_tract[merged_geo_tract['county_name']==county])
            colormap = branca.colormap.LinearColormap(
                vmin=0,
                vmax=1,
                colors=["#540B0E", "#9E2A2B", "#E09F3E", "#FFF3B0", "#335c67"],
                caption="Digital Index (%)",
            )
            
            tooltip = folium.GeoJsonTooltip(
                fields=["tract_code", "Population", "connections_above25"],
                aliases=["Tract Code:", "Population:   ", "Digital Index:"],
                localize=True,
                sticky=False,
                labels=True,
                style="""
                    background-color: #F0EFEF;
                    border: 1px solid grey;
                    border-radius: 1px;
                    box-shadow: 1px;
                """,
                max_width=800,
            )
            # st.dataframe(merged_geo['county_name'].str.contains(county))
            g = folium.GeoJson(
                merged_geo_tract[merged_geo_tract['county_name'] == county],
                style_function=lambda x: {
                    "fillColor": colormap(x["properties"]["connections_above25"])
                    if x["properties"]["connections_above25"] is not None
                    else "transparent",
                    "color": "black",
                    "fillOpacity": 0.6,
                    "weight": 0.3,
                },
                tooltip=tooltip,
            ).add_to(map)
            # Iterate over the GeoDataFrame to place state names
            for _, row in merged_geo_tract.iterrows():
                # Extract the centroid of the state's boundary for the marker's location
                centroid = row['geometry'].centroid
                folium.Marker(
                    [centroid.y, centroid.x],  # y is latitude and x is longitude
                    popup=row['tract_code'],  # The state name will appear in a popup on click
                    icon=folium.DivIcon(html=f"""<div style="font-size: 0.8rem">{row['tract_code']}</div>""")  # Or use DivIcon for a label
                ).add_to(map)
            map.add_child(colormap)

            if tract!=None:
                tract_code = tract.split(" - ")[0]
                gdf = merged_geo_tract[(merged_geo_tract['tract_code'].str.contains(tract_code)) & (merged_geo_tract['county_name'] == county)]
                style_parcels = {"weight": "3",'fillColor':"#00A8E8", "fillOpacity": 0.8,"color":"#00A8E8"}
                polygon_folium = folium.GeoJson(data=gdf, style_function=lambda x: style_parcels)
                fg.add_child(polygon_folium)
            map.add_child(colormap)
        map.add_child(folium.FitBounds(bounds))
        st_map = st_folium(map,use_container_width=True,height=600,feature_group_to_add=fg)
    
    with st.container():
        # col1, col2 = st.columns([7,1])
        # with col1:
        if county==None:
            county_code = ''
            c_table = merged_geo_county[(merged_geo_county['county_name'].str.contains(county_code))][['county_name','Population','Male', 'Female', 'White',
    'Black', 'Asian', 'Native', 'Pacific', 'Other','25+ yrs old without graduating high school',
    'Without an internet subscription, broadband of any type','Households without a desktop or laptop',
    'connections_above25',r'% of people not using internet at broadband speed',
    'Education Score', 'Employment Score','Development Score', 'Income Score',]].rename(columns={'county_name':'County:','connections_above25':'Digital Index','county_name':'County'}).sort_values(['Digital Index'],ascending=False).set_index('County').round(2)
            # multiply by 100 to get percentages
            st.dataframe(c_table)
        else:
            county_code = county
            if tract!=None:
                tract_code = tract.split(" - ")[0]
            else:
                tract_code = ''
            st.dataframe(merged_geo_tract[(merged_geo_tract['tract_code'].str.contains(tract_code)) & (merged_geo_tract['county_name'] == county_code)][['tract_code','county_name','Population','Male', 'Female', 'White',
    'Black', 'Asian', 'Native', 'Pacific', 'Other','25+ yrs old without graduating high school',
    'Without an internet subscription, broadband of any type','Households without a desktop or laptop',
    'connections_above25',r'% of people not using internet at broadband speed',
    'Education Score', 'Employment Score','Development Score', 'Income Score',]].rename(columns={'tract_code':'Census Tract','connections_above25':'Digital Index','county_name':'County'}).sort_values(['Digital Index'],ascending=False).set_index('Census Tract').round(2))
        
            
            
    # with col2:
    # #     metric = st.selectbox("Select a Metric",options=['Population','Male', 'Female', 'White',
    # #    'Black', 'Asian', 'Native', 'Pacific', 'Other','25+ yrs old without graduating high school',
    # #    'Without an internet subscription, broadband of any type','Households without a desktop or laptop',
    # #    'connections_above25',r'% of people not using internet at broadband speed',
    # #    'Education Score', 'Employment Score','Development Score', 'Income Score',])
    # #     if county==None:
    # #         county_code = ''
    # #     else:
    # #         county_code = county
    # #     st.header(f"Digital Index vs {metric}")
    # #     c = (
    # #         alt.Chart(filt[filt['county_name'].str.contains(county_code)][[metric,'connections_above25','tract_code']].rename(columns={'connections_above25':'Digital Index','tract_code':'Census Tract'}))
    # #         .mark_circle()
    # #         .encode(x=metric,y='Digital Index', color='Digital Index', tooltip=["Census Tract"])
    # #         .interactive()
    # #     )
    # #     st.altair_chart(c.interactive(), use_container_width=True)