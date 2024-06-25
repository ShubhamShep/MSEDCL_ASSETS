import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import os

# Set page config (this must be the first Streamlit command)
st.set_page_config(
    page_title="Power Infrastructure Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': '# Power Infrastructure Dashboard\n\nA dashboard to visualize power infrastructure data.'
    }
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stSelectbox, .stMultiselect {
        padding-bottom: 1rem;
    }
    .stMetric {
        padding: 0.5rem;
        background-color: #f9f9f9;
        border-radius: 0.5rem;
    }
    .sidebar-content {
        padding: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )
    return conn

# Load the data from PostgreSQL
@st.cache_data
def load_data():
    conn = get_db_connection()
    query = "SELECT * FROM  asset_data"
    data = pd.read_sql(query, conn)
    conn.close()
    return data

# Load data
data = load_data()

# Title and description
st.title("MSEDCL ASSET DASHBOARD")
st.markdown(
    """
    Welcome to the MSEDCL ASSET Dashboard. Here, you can explore various metrics and visualizations related to power infrastructure assets.
    Use the filters on the sidebar to customize the data displayed.
    """
)

# Sidebar for filtering
st.sidebar.header("Filters")
selected_region = st.sidebar.multiselect(
    "Select Region", 
    options=data["region_name"].unique(), 
    default=data["region_name"].unique(),
    help="Filter the data by selecting specific regions."
)
selected_zone = st.sidebar.multiselect(
    "Select Zone", 
    options=data["z_name"].unique(), 
    default=data["z_name"].unique(),
    help="Filter the data by selecting specific zones."
)

# Filter data
filtered_data = data[data["region_name"].isin(selected_region) & data["z_name"].isin(selected_zone)]

# Calculate totals
total_substation = filtered_data["substation"].sum()
total_dtc = filtered_data["dtc"].sum()
total_ht_pole = filtered_data["ht_pole"].sum()
total_lt_pole = filtered_data["lt_pole"].sum()

# Display metrics
st.markdown("## Key Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Substations", f"{total_substation:,}", help="Total number of substations in the filtered data.")
col2.metric("Total DTCs", f"{total_dtc:,}", help="Total number of DTCs in the filtered data.")
col3.metric("Total HT Poles", f"{total_ht_pole:,}", help="Total number of HT poles in the filtered data.")
col4.metric("Total LT Poles", f"{total_lt_pole:,}", help="Total number of LT poles in the filtered data.")

# Aggregate data by region
region_data = filtered_data.groupby("region_name").sum().reset_index()

# Create visualizations
st.markdown("## Visualizations")

st.markdown("### Distribution of Assets by Region")
fig1 = px.bar(
    region_data, x="region_name", y=["substation", "dtc", "ht_pole", "lt_pole"], 
    title="Asset Distribution by Region",
    labels={"value": "Count", "variable": "Asset Type"},
    barmode="group",
    template="plotly_white"
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### Asset Type Distribution")
asset_totals = region_data[["substation", "dtc", "ht_pole", "lt_pole"]].sum()
fig2 = px.pie(
    values=asset_totals.values, names=asset_totals.index, 
    title="Overall Asset Type Distribution",
    hole=0.3,
    template="plotly_white"
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Zone-wise Asset Comparison")
zone_data = filtered_data.groupby("z_name").sum().reset_index()
fig3 = px.bar(
    zone_data, x="z_name", y=["substation", "dtc", "ht_pole", "lt_pole"],
    title="Asset Distribution by Zone",
    labels={"value": "Count", "variable": "Asset Type"},
    barmode="group",
    template="plotly_white"
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("### Heatmap: Asset Distribution Across Regions and Zones")
heatmap_data = filtered_data.pivot_table(
    values=["substation", "dtc", "ht_pole", "lt_pole"],
    index="region_name",
    columns="z_name",
    aggfunc="sum",
    fill_value=0
)
fig4 = px.imshow(
    heatmap_data, 
    labels=dict(color="Count"),
    title="Asset Distribution Heatmap",
    template="plotly_white"
)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("### Correlation: DTCs vs Substations")
fig5 = px.scatter(
    filtered_data, x="dtc", y="substation", color="region_name", 
    hover_data=["z_name", "c_name"],
    title="Correlation between DTCs and Substations",
    template="plotly_white"
)
st.plotly_chart(fig5, use_container_width=True)

# Display raw data
st.markdown("### Raw Data")
st.dataframe(filtered_data)

# Add a download button for the filtered data
csv = filtered_data.to_csv(index=False)
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="filtered_power_infrastructure_data.csv",
    mime="text/csv",
)
