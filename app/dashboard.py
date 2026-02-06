import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.database.connection import DatabaseConnection
from src.database.repository import AuctionRepository

st.set_page_config(
    page_title="Energy Auction Results Dashboard",
    page_icon="⚡",
    layout="wide"
)

st.title("French Energy Auction Results")
st.markdown("Interactive visualization of auction data by region and technology")


@st.cache_data(ttl=300)
def load_data():
    db = DatabaseConnection()
    session = db.connect()
    repo = AuctionRepository(session)

    auctions = repo.get_all_auctions()
    db.close()

    df = pd.DataFrame([
        {
            'auction_date': a.auction_date,
            'region': a.region,
            'technology': a.technology,
            'volume_offered_mwh': float(a.volume_offered_mwh) if a.volume_offered_mwh else 0,
            'volume_allocated_mwh': float(a.volume_allocated_mwh) if a.volume_allocated_mwh else 0,
            'weighted_avg_price_eur': float(a.weighted_avg_price_eur) if a.weighted_avg_price_eur else 0,
        }
        for a in auctions
    ])

    # Map technology names to English
    tech_map = {
        'Eolien onshore': 'Onshore Wind',
        'Hydraulique': 'Hydroelectric',
        'Solaire': 'Solar',
        'Thermique': 'Thermal'
    }
    df['technology_en'] = df['technology'].map(tech_map).fillna(df['technology'])

    return df


df = load_data()

if df.empty:
    st.warning("No auction data found in the database.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# Date filter
if 'auction_date' in df.columns and df['auction_date'].notna().any():
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(df['auction_date'].min(), df['auction_date'].max()),
        min_value=df['auction_date'].min(),
        max_value=df['auction_date'].max()
    )

selected_regions = st.sidebar.multiselect(
    "Select Regions",
    options=sorted(df['region'].unique()),
    default=sorted(df['region'].unique())
)

selected_tech = st.sidebar.multiselect(
    "Select Technologies",
    options=df['technology_en'].unique(),
    default=df['technology_en'].unique()
)

# Filter data
filtered_df = df[
    (df['region'].isin(selected_regions)) &
    (df['technology_en'].isin(selected_tech))
]

if 'date_range' in dir() and len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['auction_date'] >= date_range[0]) &
        (filtered_df['auction_date'] <= date_range[1])
    ]

# Key metrics
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_allocated = filtered_df['volume_allocated_mwh'].sum()
    st.metric("Total Volume Allocated (MWh)", f"{total_allocated:,.0f}")
with col2:
    total_offered = filtered_df['volume_offered_mwh'].sum()
    st.metric("Total Volume Offered (MWh)", f"{total_offered:,.0f}")
with col3:
    avg_price = filtered_df['weighted_avg_price_eur'].mean()
    st.metric("Avg Price (EUR/MWh)", f"{avg_price:.2f}")
with col4:
    num_auctions = len(filtered_df)
    st.metric("Number of Records", f"{num_auctions:,}")

st.markdown("---")

# Charts row 1
col1, col2 = st.columns(2)

with col1:
    st.subheader("Volume Allocated by Region")
    region_data = filtered_df.groupby('region')['volume_allocated_mwh'].sum().reset_index()
    region_data = region_data.sort_values('volume_allocated_mwh', ascending=True)
    fig1 = px.bar(
        region_data,
        x='volume_allocated_mwh',
        y='region',
        orientation='h',
        color='volume_allocated_mwh',
        color_continuous_scale='Viridis',
        labels={'volume_allocated_mwh': 'Volume (MWh)', 'region': 'Region'}
    )
    fig1.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig1, width='stretch')

with col2:
    st.subheader("Volume Distribution by Technology")
    tech_data = filtered_df.groupby('technology_en')['volume_allocated_mwh'].sum().reset_index()
    fig2 = px.pie(
        tech_data,
        values='volume_allocated_mwh',
        names='technology_en',
        color='technology_en',
        color_discrete_map={
            'Onshore Wind': '#2E86AB',
            'Solar': '#F6AE2D',
            'Hydroelectric': '#26547C',
            'Thermal': '#EF476F'
        }
    )
    fig2.update_traces(textposition='inside', textinfo='percent+label')
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, width='stretch')

# Charts row 2
col1, col2 = st.columns(2)

with col1:
    st.subheader("Average Price by Technology")
    price_data = filtered_df.groupby('technology_en')['weighted_avg_price_eur'].mean().reset_index()
    price_data = price_data.sort_values('weighted_avg_price_eur', ascending=False)
    fig3 = px.bar(
        price_data,
        x='technology_en',
        y='weighted_avg_price_eur',
        color='technology_en',
        color_discrete_map={
            'Onshore Wind': '#2E86AB',
            'Solar': '#F6AE2D',
            'Hydroelectric': '#26547C',
            'Thermal': '#EF476F'
        },
        labels={'weighted_avg_price_eur': 'Price (EUR/MWh)', 'technology_en': 'Technology'}
    )
    fig3.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig3, width='stretch')

with col2:
    st.subheader("Volume by Technology (Sunburst)")
    fig4 = px.sunburst(
        filtered_df,
        path=['technology_en', 'region'],
        values='volume_allocated_mwh',
        color='technology_en',
        color_discrete_map={
            'Onshore Wind': '#2E86AB',
            'Solar': '#F6AE2D',
            'Hydroelectric': '#26547C',
            'Thermal': '#EF476F'
        }
    )
    fig4.update_layout(height=400)
    st.plotly_chart(fig4, width='stretch')

# Stacked bar chart
st.subheader("Volume by Region and Technology")
fig5 = px.bar(
    filtered_df,
    x='region',
    y='volume_allocated_mwh',
    color='technology_en',
    color_discrete_map={
        'Onshore Wind': '#2E86AB',
        'Solar': '#F6AE2D',
        'Hydroelectric': '#26547C',
        'Thermal': '#EF476F'
    },
    barmode='stack',
    labels={'volume_allocated_mwh': 'Volume (MWh)', 'region': 'Region', 'technology_en': 'Technology'}
)
fig5.update_layout(height=500, xaxis_tickangle=-45)
st.plotly_chart(fig5, width='stretch')

# Time series if multiple dates exist
unique_dates = filtered_df['auction_date'].nunique()
if unique_dates > 1:
    st.subheader("Volume Over Time")
    time_data = filtered_df.groupby(['auction_date', 'technology_en'])['volume_allocated_mwh'].sum().reset_index()
    fig6 = px.line(
        time_data,
        x='auction_date',
        y='volume_allocated_mwh',
        color='technology_en',
        color_discrete_map={
            'Onshore Wind': '#2E86AB',
            'Solar': '#F6AE2D',
            'Hydroelectric': '#26547C',
            'Thermal': '#EF476F'
        },
        markers=True,
        labels={'volume_allocated_mwh': 'Volume (MWh)', 'auction_date': 'Date', 'technology_en': 'Technology'}
    )
    fig6.update_layout(height=400)
    st.plotly_chart(fig6, width='stretch')

# Scatter plot
st.subheader("Volume vs Price Analysis")
fig7 = px.scatter(
    filtered_df,
    x='volume_allocated_mwh',
    y='weighted_avg_price_eur',
    color='technology_en',
    hover_data=['region', 'auction_date'],
    color_discrete_map={
        'Onshore Wind': '#2E86AB',
        'Solar': '#F6AE2D',
        'Hydroelectric': '#26547C',
        'Thermal': '#EF476F'
    },
    labels={
        'volume_allocated_mwh': 'Volume Allocated (MWh)',
        'weighted_avg_price_eur': 'Price (EUR/MWh)',
        'technology_en': 'Technology'
    }
)
fig7.update_layout(height=500)
st.plotly_chart(fig7, width='stretch')

# Data table
st.subheader("Detailed Data")
display_df = filtered_df[[
    'auction_date', 'region', 'technology_en',
    'volume_offered_mwh', 'volume_allocated_mwh', 'weighted_avg_price_eur'
]].rename(columns={
    'auction_date': 'Date',
    'region': 'Region',
    'technology_en': 'Technology',
    'volume_offered_mwh': 'Offered (MWh)',
    'volume_allocated_mwh': 'Allocated (MWh)',
    'weighted_avg_price_eur': 'Price (EUR/MWh)'
})
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Data source: French Energy Auction Results Database")
