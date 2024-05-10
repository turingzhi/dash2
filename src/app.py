import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import matplotlib as mpl
import plotly.express as px
import plotly.graph_objects as go

import seaborn as sns

from dash import Dash
from dash import dcc, html
from dash.dependencies import Input, Output

import calmap
# import calplot
import calendar

import geopandas as gpd


# Load the GeoJSON file
geojson_file = 'Boundaries - Community Areas (current).geojson'  # Replace 'your_geojson_file.geojson' with the actual file path
gdf = gpd.read_file(geojson_file)

# Check the structure of the GeoDataFrame
#print(gdf.head())

# Extract community area information
community_data = gdf[['area_numbe', 'community']].drop_duplicates()

# Convert community data to a dictionary for mapping
community = dict(zip(community_data['area_numbe'], community_data['community']))



### read the dataset
#Define a list of URLs
urls = [
    #'https://drive.google.com/file/d/1kB7Q4vJFOPOuvYgjUh1D6ekqJxNXfFut/view?usp=share_link',
    #'https://drive.google.com/file/d/1c8RSRc0_bEwB8o0jmxEGP3SNlVGOLtKX/view?usp=share_link',
    #'https://drive.google.com/file/d/1vX1IZg2v59m3bbXbiyOz9BigBhYejcnq/view?usp=share_link',
    'https://drive.google.com/file/d/1jbsg9iNAqH0wHi9JvUyMh3W058vtZgMu/view?usp=share_link'
  
    # Add more URLs as needed
]

# Initialize an empty list to store DataFrames
dfs = []

# Loop through each URL
for url in urls:
    # Modify the URL to use the direct download link
    url = 'https://drive.google.com/uc?id=' + url.split('/')[-2]
    
    # Read the CSV file directly from the URL into a DataFrame
    df1 = pd.read_csv(url)
    
    # Append the DataFrame to the list
    dfs.append(df1)

# Concatenate all DataFrames into a single DataFrame
df = pd.concat(dfs, ignore_index=True)
df['Trip Start Timestamp'] = pd.to_datetime(df['Trip Start Timestamp'])

app2 = Dash(__name__)
server = app2.server

app2.layout = html.Div([
    dcc.Slider(
        id='hour-slider',
        min=0,
        max=23,
        value=12,
        marks={i: str(i) for i in range(24)},
        step=1,
    ),
    dcc.Graph(id='median-miles-graph')
])

@app2.callback(
    Output('median-miles-graph', 'figure'),
    Input('hour-slider', 'value')
)
def update_graph(selected_hour):
    # Filter the DataFrame for the selected hour
    filtered_df = df[df['Trip Start Timestamp'].dt.hour == selected_hour]

    # Calculate the median Trip Miles for each community area
    median_miles = filtered_df.groupby('Pickup Community Area')['Trip Miles'].median().reset_index()

    # Sort by median Trip Miles and select the top 14 areas
    top_areas = median_miles.sort_values(by='Trip Miles', ascending=False).head(14)

    # Create a new column combining the community area number and name
    top_areas['Community Info'] = top_areas['Pickup Community Area'].apply(
        lambda x: f"{x} - {community.get(x, 'Unknown')}"
    )

    # Create a line plot using the new column as x-axis labels
    fig = px.line(
        top_areas,
        x='Community Info',
        y='Trip Miles',
        line_shape='linear',  # Line shape: options are 'linear', 'spline', 'vhv', 'hvh', 'vh', 'hv'
        markers=True,  # Add markers
        labels={'Community Info': 'Community'}  # Customize axis labels
    )

    # Update the line style of the plot, changing the color to black
    fig.update_traces(line=dict(width=4, color="black"))

    # Add a yellow dashed line on the y-axis and label it "=15m"
    fig.add_shape(
        type='line',
        x0=0, x1=1,  # Range of the x-axis, represented in relative coordinates (0 for start, 1 for end)
        y0=15, y1=15,  # Position on the y-axis (fixed at 15 km)
        line=dict(
            color='#FFC700',
            width=2,  # Width of the dashed line
            dash='dash'  # 'dash' represents a dashed line
        ),
        xref='paper',  # Use 'paper' coordinate system (0~1)
        yref='y'  # Use the y-axis coordinates of the plot
    )

    # Add a new scatter plot, marking points where Trip Miles is greater than 15
    fig.add_scatter(
        x=top_areas[top_areas['Trip Miles'] > 15]['Community Info'],
        y=top_areas[top_areas['Trip Miles'] > 15]['Trip Miles'],
        mode='markers',
        marker=dict(size=10, color='#FFC700', symbol='circle'),  # Filled circle
        name='> 15 km'
    )

    return fig

if __name__ == '__main__':
    app2.run_server(mode='inline')