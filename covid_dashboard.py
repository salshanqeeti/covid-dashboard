# importing libraries
import streamlit as st
import pandas as pd
from plotly import express as px

# creating the app
st.set_page_config(layout="wide")
st.title("COVID Country Map")

st.write(
    "Explore reported COVID-19 infections, recoveries, and deaths."
)

# choosing daily or cumulative counts
display = st.radio(
    "Choose a display",
    ["Daily", "Cumulative"]
)

# choosing the measure
measure = st.selectbox(
    "Choose a measure",
    ["Confirmed infections", "Recovered", "Deaths"]
)

# setting the data location
base_url = (
    "https://raw.githubusercontent.com/CSSEGISandData/"
    "COVID-19/master/csse_covid_19_data/"
)

# choosing the correct file
if measure == "Confirmed infections":
    file_name = "time_series_covid19_confirmed_global.csv"

elif measure == "Recovered":
    file_name = "time_series_covid19_recovered_global.csv"

    st.info(
        "Recovery reporting was discontinued in August 2021. "
        "This view ends on August 3, 2021, and coverage is incomplete."
    )

else:
    file_name = "time_series_covid19_deaths_global.csv"

# loading cumulative counts
covid = pd.read_csv(
    base_url + "csse_covid_19_time_series/" + file_name
)

# removing columns not needed for country totals
covid = covid.drop(
    columns=["Province/State", "Lat", "Long"]
)

# adding together provinces and states within each country
covid = covid.groupby("Country/Region").sum(min_count=1)

# putting dates in rows and countries in columns
covid = covid.T

# converting the dates
covid.index = pd.to_datetime(
    covid.index,
    format="%m/%d/%y"
)

covid.index.name = "Date"

# limiting recovery dates to before reporting stopped
if measure == "Recovered":
    covid = covid.loc[:"2021-08-03"]

# calculating daily changes
if display == "Daily":
    covid = covid.diff()

    # removing the first day because there is no previous day
    covid = covid.iloc[1:]

# choosing a date
selected_date = st.date_input(
    "Choose a date",
    value=covid.index[-1].date(),
    min_value=covid.index[0].date(),
    max_value=covid.index[-1].date()
)

# getting counts for the selected date
map_data = covid.loc[
    pd.Timestamp(selected_date)
].reset_index()

map_data.columns = ["Country", "Count"]

# loading country codes for the map
lookup = pd.read_csv(
    base_url + "UID_ISO_FIPS_LookUp_Table.csv"
)

# keeping country-level entries
lookup = lookup[
    lookup["Province_State"].isna()
    & lookup["Admin2"].isna()
]

# keeping country names and map codes
lookup = lookup[["Country_Region", "iso3"]]
lookup.columns = ["Country", "iso3"]

# matching country codes with the counts
map_data = map_data.merge(
    lookup,
    on="Country"
)

# removing entries without a count or map code
map_data = map_data.dropna(
    subset=["Count", "iso3"]
)

# choosing one or more countries
countries = st.multiselect(
    "Filter by country",
    options=sorted(map_data["Country"]),
    default=[]
)

st.write(
    "Leave the selection empty to show all available countries. "
    "Select one or more countries to filter the map."
)

# filtering only when countries are selected
if len(countries) > 0:
    map_data = map_data[
        map_data["Country"].isin(countries)
    ]

# creating the purple map
fig = px.choropleth(
    map_data,
    locations="iso3",
    locationmode="ISO-3",
    color="Count",
    hover_name="Country",
    hover_data={
        "iso3": False,
        "Count": ":,.0f"
    },
    color_continuous_scale="Purples",
    projection="natural earth",
    title=display + " " + measure + " on " + str(selected_date)
)

# displaying the map
st.plotly_chart(
    fig,
    use_container_width=True
)

# optionally displaying the numbers
if st.checkbox("Show data table"):
    st.dataframe(
        map_data[["Country", "Count"]]
    )

# explaining the data source
st.caption(
    "Source: Johns Hopkins University CSSE COVID-19 repository. "
    "Confirmed infections and deaths cover January 22, 2020 "
    "through March 9, 2023. These are historical data."
)

st.caption(
    "Daily values are net changes in reported cumulative counts. "
    "Negative values can reflect corrections. Reporting delays "
    "and differences in testing affect comparisons. "
    "Counts are not adjusted for population."
)

st.caption(
    "Recovery reporting is incomplete. Countries without usable "
    "data or matching map boundaries may remain unshaded."
)