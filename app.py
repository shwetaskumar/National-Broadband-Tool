<<<<<<< HEAD
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium,folium_static
from streamlit.components.v1 import html
import branca
st.set_page_config(layout="wide")
 
def nav_page(page_name, timeout_secs=3):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)

def go_to_page(state,state_code):
    st.session_state['selected_state'] = state
    st.session_state['selected_state_code'] = state_code
    nav_page('state')
@st.cache_resource
def get_df():
    states_data = pd.read_parquet("DATA/data_2021_states.parquet")
    states_geo = gpd.read_file("https://raw.githubusercontent.com/shwetaskumar/NBTShapes/main/SHAPES/us-state-boundaries.geojson")
    states_merged = states_geo.merge(states_data, right_on='state_code', left_on='geoid', how='left')
    return states_merged

STATES = {'Alabama': '01',
 'Alaska': '02',
 'Arizona': '04',
 'Arkansas': '05',
 'California': '06',
 'Colorado': '08',
 'Connecticut': '09',
 'District of Columbia': '11',
 'Delaware': '10',
 'Florida': '12',
 'Georgia': '13',
 'Hawaii': '15',
 'Idaho': '16',
 'Illinois': '17',
 'Indiana': '18',
 'Iowa': '19',
 'Kansas': '20',
 'Kentucky': '21',
 'Louisiana': '22',
 'Maine': '23',
 'Maryland': '24',
 'Massachusetts': '25',
 'Michigan': '26',
 'Minnesota': '27',
 'Mississippi': '28',
 'Missouri': '29',
 'Montana': '30',
 'Nebraska': '31',
 'Nevada': '32',
 'New Hampshire': '33',
 'New Jersey': '34',
 'New Mexico': '35',
 'New York': '36',
 'North Carolina': '37',
 'North Dakota': '38',
 'Ohio': '39',
 'Oklahoma': '40',
 'Oregon': '41',
 'Pennsylvania': '42',
 'Puerto Rico': '72',
 'Rhode Island': '44',
 'South Carolina': '45',
 'South Dakota': '46',
 'Tennessee': '47',
 'Texas': '48',
 'Utah': '49',
 'Vermont': '50',
 'Virginia': '51',
 'Washington': '53',
 'West Virginia': '54',
 'Wisconsin': '55',
 'Wyoming': '56'}
st.title('National Broadband Tool')

# Sidebar
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 50px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)


cols1,cols2 = st.columns([3,4])
data = get_df()
with cols1:
    st.markdown('**Welcome to the National Broadband Tool Dashboard, your interactive guide to transforming rural connectivity. Use this powerful platform to uncover key broadband investment opportunities in areas poised for socio-economic growth. Navigate our maps, dive into insightful charts, and quantify the profound changes high-speed internet access can bring. This tool is your first step in crafting compelling proposals that highlight the tangible benefits of broadband expansion and secure the necessary funding to bridge the digital divide.**')
    st.markdown(':blue[The Digital Index quantifies broadband access by the share of connections above 25 Mbps on a scale from 0 to 1; areas with values near 0, **shown in darker red, are priority zones** for network enhancements due to their limited high-speed connectivity.]')
    selected_state = st.selectbox("Select a State",list(STATES.keys()))
    selected_state_code = STATES[selected_state]
    st.button("Go to State", on_click=go_to_page, args=[selected_state,selected_state_code])
with cols2:
    
    colormap = branca.colormap.LinearColormap(
            vmin=data["connections_above25"].quantile(0.0),
            vmax=data["connections_above25"].quantile(1),
            colors=["#9d0208", "#dc2f02", "#f48c06", "#ffba08", "#d7fff1"],
            caption="Digital Index (%)",
        )
    tooltip = folium.GeoJsonTooltip(
        fields=["name","connections_above25"],
        aliases=['State:',"Digital Index:"],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0EFEF;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
        max_width=800,
    )
    
    map = folium.Map(location=[38, -96.5], zoom_start=4, tiles='CartoDB positron')
    g = folium.GeoJson(
            data,
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
    for _, row in data.iterrows():
        # Extract the centroid of the state's boundary for the marker's location
        centroid = row['geometry'].centroid
        folium.Marker(
            [centroid.y, centroid.x],  # y is latitude and x is longitude
            popup=row['name'],  # The state name will appear in a popup on click
            icon=folium.DivIcon(html=f"""<div style="font-size: 0.8rem">{row['name']}</div>""")  # Or use DivIcon for a label
        ).add_to(map)
    map.add_child(colormap)
    # fg = folium.FeatureGroup(name="State bounds")
    # fg.add_child(g)
    st_map = folium_static(map,height=600)
# if 'selected_state' not in st.session_state:
#     st.session_state['selected_state'] = selected_state
=======
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium,folium_static
from streamlit.components.v1 import html
import branca
st.set_page_config(layout="wide")
 
def nav_page(page_name, timeout_secs=3):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)

def go_to_page(state,state_code):
    st.session_state['selected_state'] = state
    st.session_state['selected_state_code'] = state_code
    nav_page('state')
@st.cache_resource
def get_df():
    states_data = pd.read_parquet("DATA/data_2021_states.parquet")
    states_geo = gpd.read_file("https://raw.githubusercontent.com/shwetaskumar/NBTShapes/main/SHAPES/us-state-boundaries.geojson")
    states_merged = states_geo.merge(states_data, right_on='state_code', left_on='geoid', how='left')
    return states_merged

STATES = {'Alabama': '01',
 'Alaska': '02',
 'Arizona': '04',
 'Arkansas': '05',
 'California': '06',
 'Colorado': '08',
 'Connecticut': '09',
 'District of Columbia': '11',
 'Delaware': '10',
 'Florida': '12',
 'Georgia': '13',
 'Hawaii': '15',
 'Idaho': '16',
 'Illinois': '17',
 'Indiana': '18',
 'Iowa': '19',
 'Kansas': '20',
 'Kentucky': '21',
 'Louisiana': '22',
 'Maine': '23',
 'Maryland': '24',
 'Massachusetts': '25',
 'Michigan': '26',
 'Minnesota': '27',
 'Mississippi': '28',
 'Missouri': '29',
 'Montana': '30',
 'Nebraska': '31',
 'Nevada': '32',
 'New Hampshire': '33',
 'New Jersey': '34',
 'New Mexico': '35',
 'New York': '36',
 'North Carolina': '37',
 'North Dakota': '38',
 'Ohio': '39',
 'Oklahoma': '40',
 'Oregon': '41',
 'Pennsylvania': '42',
 'Puerto Rico': '72',
 'Rhode Island': '44',
 'South Carolina': '45',
 'South Dakota': '46',
 'Tennessee': '47',
 'Texas': '48',
 'Utah': '49',
 'Vermont': '50',
 'Virginia': '51',
 'Washington': '53',
 'West Virginia': '54',
 'Wisconsin': '55',
 'Wyoming': '56'}
st.title('National Broadband Tool')

# Sidebar
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 50px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)


cols1,cols2 = st.columns([3,4])
data = get_df()
with cols1:
    st.markdown('**Welcome to the National Broadband Tool Dashboard, your interactive guide to transforming rural connectivity. Use this powerful platform to uncover key broadband investment opportunities in areas poised for socio-economic growth. Navigate our maps, dive into insightful charts, and quantify the profound changes high-speed internet access can bring. This tool is your first step in crafting compelling proposals that highlight the tangible benefits of broadband expansion and secure the necessary funding to bridge the digital divide.**')
    st.markdown(':blue[The Digital Index quantifies broadband access by the share of connections above 25 Mbps on a scale from 0 to 1; areas with values near 0, **shown in darker red, are priority zones** for network enhancements due to their limited high-speed connectivity.]')
    selected_state = st.selectbox("Select a State",list(STATES.keys()))
    selected_state_code = STATES[selected_state]
    st.button("Go to State", on_click=go_to_page, args=[selected_state,selected_state_code])
with cols2:
    
    colormap = branca.colormap.LinearColormap(
            vmin=data["connections_above25"].quantile(0.0),
            vmax=data["connections_above25"].quantile(1),
            colors=["#9d0208", "#dc2f02", "#f48c06", "#ffba08", "#d7fff1"],
            caption="Digital Index (%)",
        )
    tooltip = folium.GeoJsonTooltip(
        fields=["name","connections_above25"],
        aliases=['State:',"Digital Index:"],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0EFEF;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
        max_width=800,
    )
    
    map = folium.Map(location=[38, -96.5], zoom_start=4, tiles='CartoDB positron')
    g = folium.GeoJson(
            data,
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
    for _, row in data.iterrows():
        # Extract the centroid of the state's boundary for the marker's location
        centroid = row['geometry'].centroid
        folium.Marker(
            [centroid.y, centroid.x],  # y is latitude and x is longitude
            popup=row['name'],  # The state name will appear in a popup on click
            icon=folium.DivIcon(html=f"""<div style="font-size: 0.8rem">{row['name']}</div>""")  # Or use DivIcon for a label
        ).add_to(map)
    map.add_child(colormap)
    # fg = folium.FeatureGroup(name="State bounds")
    # fg.add_child(g)
    st_map = folium_static(map,height=600)
# if 'selected_state' not in st.session_state:
#     st.session_state['selected_state'] = selected_state
>>>>>>> d1c0ee61b5c2f86ff0a9169997fc2d87d96a6519
#     st.session_state['selected_state_code'] = STATES[selected_state]