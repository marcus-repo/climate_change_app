import streamlit as st
import pandas as pd
import numpy as np
import base64
from collections import OrderedDict
import requests
import plotly.express as px


## Page and Title
st.set_page_config(page_title="Climate Change Dashboard", layout='wide')
st.title(':grey[CO2 Emissions - Top 10 World Economies]')
st.divider()

## Default Parameters for user selection (sidebar) and data retrieval (world bank api)
# default dict of indicators: CO2 emissions (kt), CO2 emissions (metric tons per capita)
indicator_default = OrderedDict([('CO2 emissions (kt)','EN.ATM.CO2E.KT'), 
                     ('CO2 emissions (metric tons per capita)','EN.ATM.CO2E.PC')])

# default dict of all countries of interest
country_default = OrderedDict([('Canada', 'CAN'), ('United States', 'USA'), 
  ('Brazil', 'BRA'), ('France', 'FRA'), ('India', 'IND'), ('Italy', 'ITA'), 
  ('Germany', 'DEU'), ('United Kingdom', 'GBR'), ('China', 'CHN'), ('Japan', 'JPN')])

# default date range
year_default = (1990, 2020)


## Sidebar
with st.sidebar:
    # Content description
    st.header("Content")
    st.write("This dasboard shows CO2 Emissions from the Top 10 World Economies.")
    url = "https://data.worldbank.org/indicator"
    st.header("Datasource")
    st.write("[World Bank Indicators](%s)" % url)
    st.divider()

    # User Selections: Indicator, Country, Years
    # Indicator
    with st.popover("Indicators",use_container_width=True):
        indicator_selection = st.radio(
            "Select Indicator",
            [k for k in indicator_default.keys()],
        )
    # Country
    with st.popover("Countries",use_container_width=True):
        # country selection - create dropdown menu for country selection
        country_selection = st.multiselect("Countries", 
                                           country_default.keys(), 
                                           country_default.keys())
    # Years
    with st.popover("Years", use_container_width=True):
        # Year selection - Create slider for year range selection
        year_selection = st.slider('Years', year_default[0], 
                                   year_default[1], 
                                   (year_default[0], year_default[1]))
    st.divider()

    # Author info
    st.header("Author")
    linkedin, github = st.columns(2)
    linkedin.markdown(
        """<a href="https://de.linkedin.com/in/marcus-zeug/">
        <img src="data:image/png;base64,{}" width="80">
        </a>""".format(
            base64.b64encode(open("files/linkedinlogo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )
    github.markdown(
        """<a href="https://github.com/marcus-repo">
        <img src="data:image/png;base64,{}" width="75">
        </a>""".format(
            base64.b64encode(open("files/githublogo.png", "rb").read()).decode()
        ),
        unsafe_allow_html=True,
    )

## World Bank API Data Retrieval
@st.cache_data
def get_data(indicator_filter, country_filter, year_filter):
    """Retrieves an indicator from world bank api for multiple countries in a given year range.
       1. Request data with URL from world bank in JSON format
       2. Convert JSON to dataframe

       :params indicator_filter (str): A single World Bank Indicator, e. g. 'EN.ATM.CO2E.KT'
       :params country_filter (str): Semicolon separated string of countries, e. g. 'usa;can'
       :params year_filter (tuple): (start year, end year), e. g. (1990, 2020)
       :return (pd.DataFrame): Dataframe with indicator, countries and values 
    """

    #pull data from World Bank API, example:
    #https://api.worldbank.org/v2/countries/can;usa;bra;fra;ind;ita;deu;gbr;chn;jpn/indicators/AG.LND.FRST.ZS?date=1990:2015&per_page=1000&format=json
    
    url = f"https://api.worldbank.org/v2/countries/{country_filter}/indicators/{indicator_filter}?date={year_filter[0]}:{year_filter[1]}&per_page=1000&format=json"
    try:
        r = requests.get(url)
        data = r.json()[1]

        for i, value in enumerate(data):
            value['indicator'] = value['indicator']['value']
            value['country'] = value['country']['value']
    except:
        st.write(f'could not load data: {indicator_filter}')
    
    return pd.DataFrame(data).sort_values(by='date')

# Re-shape user selection (from sidebar) to meet world bank api
indicator_filter = indicator_default[indicator_selection]
# if user de-selects all countries, use default country list
if country_selection == []:
    country_filter = ';'.join([country_default[k].lower() for k in country_default])
else:
    country_filter = ';'.join([country_default[k].lower() for k in country_selection])
year_filter = year_selection

# get data from world bank api
df = get_data(indicator_filter, country_filter, year_filter)


## Create charts for Dashboard
# map each country to a specific color to have colors aligned across charts 
# https://plotly.com/python/discrete-color/ 
cmap = dict(zip(df["country"].unique(), px.colors.qualitative.Pastel))

# line chart
line_chart = px.line(df, x='date', y='value', color='country', color_discrete_map=cmap)
line_chart.update_traces(line=dict(width=3.0))
line_chart.update_xaxes(showgrid=False)
line_chart.update_layout(
    title=dict(text=f"{indicator_selection} - Year {year_selection[0]} to {year_selection[1]} ", 
               font=dict(size=50), font_color='black'),
    xaxis_title="",
    yaxis_title="",
    legend_title="Countries",
    title_font_size=24,
    xaxis = dict(tickfont = dict(size=20)),
    yaxis = dict(tickfont = dict(size=16)),
    legend=dict(font=dict(size= 16))

)
# pie chart
max_year = df['date'].max()
pie_chart = px.pie(df[df['date'] == max_year], values='value', names='country', 
                   color='country', color_discrete_map=cmap, hole=0.3, labels={'country':'country'})
pie_chart.update_traces(textposition='inside', hoverinfo='label+percent', 
                        textinfo='percent+label', textfont_size=20)
pie_chart.update_layout(
    title=dict(text=f"{indicator_selection} - Year {max_year}", font=dict(size=50), font_color='black'),
    xaxis_title="",
    yaxis_title="",
    legend_title="Countries",
    title_font_size=24,
    xaxis = dict(tickfont = dict(size=20)),
    yaxis = dict(tickfont = dict(size=20)),
    legend=dict(font=dict(size= 16)),
    showlegend=False

)
# bar chart
bar_chart = px.bar(df[df['date'] == max_year].sort_values(by='value', ascending=False), 
                   x='value', y='country', color='country', text='value',
                   color_discrete_map=cmap, orientation='h')
bar_chart.update_traces(texttemplate='%{text:.1f}', textposition='outside', textfont_size=16)
bar_chart.update_xaxes(showticklabels=False)
bar_chart.update_layout(
    title=dict(text=f"{indicator_selection} - Year {max_year}", font=dict(size=50), font_color='black'),
    xaxis_title="",
    yaxis_title="",
    legend_title="Countries",
    title_font_size=24,
    xaxis = dict(tickfont = dict(size=20), tickformat=".1f"),
    yaxis = dict(tickfont = dict(size=16)),
    showlegend=False
    #legend=dict(font=dict(size= 16))

)


## Plot charts
chart1, chart2 = st.columns([1,1])
first_indicator_key = next(iter(indicator_default))
if indicator_selection == first_indicator_key:
    chart1.plotly_chart(pie_chart, use_container_width=True)
else:
    chart1.plotly_chart(bar_chart, use_container_width=True)
chart2.plotly_chart(line_chart, use_container_width=True)

st.divider()

## Download data as csv
@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(df)

st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name=f"{indicator_filter}.csv",
    mime="text/csv",
)