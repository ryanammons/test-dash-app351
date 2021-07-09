import numpy as np
import pandas as pd
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from jupyter_dash import JupyterDash
from dash.dependencies import Input, Output
import folium
import json
import pathlib
import fiona
import folium
import os
from folium.plugins import MarkerCluster
from folium.plugins import Draw
from shapely.geometry import LineString
import geopandas as gpd
pd.options.mode.chained_assignment = None

############################################################################################################################################
### Intro ###

# BRI Country Cleaning
cntry = pd.read_excel('BRIcountrylist1.xlsx')
cntry = cntry[['Country', 'iso_alpha', 'Region', 'Income class', 'MoU', 'Year']]
cntry_new = cntry.dropna(axis=0)
cntry_new['MoU'] = cntry_new['MoU'].astype(int)
cntry_new['Year'] = cntry_new['Year'].astype(int)
cntry_new = cntry_new.sort_values(by='Year', ascending=True)
# BRI Country Plot Fig. 1
cntry_fig = px.choropleth(cntry_new, locations="iso_alpha", template = 'plotly_dark',
                          color='MoU',
                          animation_frame = 'Year',
                          hover_name='Country',
                          hover_data = ['Region', 'Income class'],
                          range_color = [2013, 2021], # data to be displayed when mousing over the map
                          color_continuous_scale=px.colors.sequential.Plasma
                          )
cntry_fig.update_layout(title_text='Years of Countries Signing the BRI Memorandum of Understanding, 2013-2021')
############################################################################################################################################
### Diplomacy ###

# Diplomacy Cleaning
diplo_df = pd.read_excel('ChinesePublicDiplomacy.xlsx')
diplo_df.rename(columns = {'receiving_country':'country', 'confucius_institutes':'con_inst',
                           'sister_cities_established':'sis_city', 'government_visits':'gov_visit', 'military_visits':'mil_visit',
                           'total_elite_visits':'elite_visit', 'ambassador_op_eds':'ambOpEd', 'journalist_visits':'journ_visit',
                           'media_partnerships':'media_partn', 'outbound_chinese_students':'out_stud',
                           'inbound_students_to_china':'in_stud'}, inplace=True)
df = diplo_df.groupby('year').sum().reset_index()
df = df.drop(index=[17,18])

# Diplomacy Countries Fig. 2
df2 = diplo_df.groupby('country').sum().reset_index()
df2 = df2.drop(['year', 'out_stud', 'in_stud'], axis=1)
df2.set_index(['country'], inplace=True)
df2['sum'] = df2.sum(axis=1)
sort = df2.sort_values(by='sum', ascending=False)
sort = sort.head(10).reset_index()
diplo_fig = go.Figure(go.Bar(
    x=sort['sum'],
    y=sort['country'],
    orientation='h'))
diplo_fig.update_layout(title_text='Top Countries for China Diplomacy', template = 'plotly_dark')

# Media Fig. 3
labels = ['Ambassador OpEds', 'Journalist Visits', 'Media Partnerships']
values = [71, 539, 66]
media_fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
media_fig.update_layout(title_text='Distribution of Diplomatic Media Actions', template = 'plotly_dark')

# Diplomatic Visits Fig. 4
visit_fig = go.Figure()
visit_fig.add_trace(go.Bar(name='Government Visit', x=df['year'], y=df['gov_visit']))
visit_fig.add_trace(go.Bar(name='Military Visit', x=df['year'], y=df['mil_visit']))
visit_fig.add_trace(go.Bar(name='Elite Visit', x=df['year'], y=df['elite_visit']))
visit_fig.add_trace(go.Bar(name='Journalist Visits', x=df['year'], y=df['journ_visit']))
visit_fig.update_layout(barmode='relative', xaxis_tickangle=75, title_text='Types of Diplomatic Visits', template = 'plotly_dark')

# Exchange Students Fig. 5
stud_fig = go.Figure()
stud_fig.add_trace(go.Scatter(x=df['year'], y=df['out_stud'], mode='lines', name='Outbound Exchange Students'))
stud_fig.add_trace(go.Scatter(x=df['year'], y=df['in_stud'], mode='lines', name='Inbound Exchange Students'))
stud_fig.update_layout(barmode='relative', title_text='Inbound vs. Outbound Chinese Exchange Students, 2000-2016', template = 'plotly_dark')

# Coercive Actions
coerComp_df = pd.read_excel('coerciveCCPforgComp.xlsx')
coerGov_df = pd.read_excel('coerciveCCPforgGov.xlsx')
action_counts = coerComp_df['Coercive_Action'].value_counts()
apol_counts = coerComp_df['Apology_Compliance'].value_counts()
# Fig. 6
compAction_fig = px.pie(names=action_counts.index, values=action_counts.values, title='Chinese Coercive Actions Against Foreign Companies', template = 'plotly_dark')
# Fig. 7
compApol_fig = px.pie(names=apol_counts.index, values=apol_counts.values, title='Did the foreign company publicly apologize or meet demands?', template = 'plotly_dark')
############################################################################################################################################

### Investments ###

bri = pd.read_csv('bri_final_to_dash.csv')
# By Sector and Subsector Fig. 8
cross = pd.crosstab(bri.Sector, bri.Subsector)
data = []
for x in cross.columns:
    data.append(go.Bar(name=str(x), x=cross.index, y=cross[x]))
sectorbar = go.Figure(data)
sectorbar.update_layout(barmode = 'stack', xaxis_tickangle=75, title='# of Investments by Sector and Subsector', template = 'plotly_dark')

# By Sector Fig. 9
value_counts = bri['Sector'].value_counts()
chn_investments_fig = px.pie(names=value_counts.index, values=value_counts.values, title='Chinese Foreign Investments by Sector', template = 'plotly_dark')


# By countries Fig. 10
mappy = go.Figure(data=go.Choropleth(
    locations = bri['Iso_alpha'],
    z = bri['Counts'],
    text = bri['Country'],
    colorscale = 'solar',
    autocolorscale=False,
    reversescale=True,
    marker_line_color='white',
    marker_line_width=0.5,
    #colorbar_tickprefix = '$',
    colorbar_title = '# of Chinese Investments',
))
mappy.update_layout(
    title_text='Map of Chinese Investments',
    template = 'plotly_dark',
    geo=dict(
        showframe=False,
        showcoastlines=True,
        projection_type='equirectangular'
    )
)

# Sunburst Fig. 11
burst = px.sunburst(bri, path=['Region','Sector','Subsector'], values='Investment_Count', color = 'Region',
                    title='Chinese Foreign Investment by Region', color_discrete_map={'Sub-Saharan Africa':'#a6d96a','East Asia':'#d9ef8b','West Asia':'#dfc27d',
                                                                                      'Arab Middle East and North Africa':'#bf812d', 'South America':'#8c510a',
                                                                                      'Europe':'#8c510a', 'North America':'#b30000', 'Australia':'#d7301f'})
burst.update_traces(insidetextorientation='radial')
burst.update_layout(
    grid= dict(columns=4, rows=5),
    margin = dict(t=25, l=0, r=0, b=0), template = 'plotly_dark'
)
############################################################################################################################################

### Trade ###

# Trade: US vs. China Fig. 12
pd.options.plotting.backend = "plotly"
trade = pd.read_excel('ChinaTradeOverview.xlsx')
tradeplot = trade.plot(x='Year', y=['CN_ExtoAfr', 'CN_IMfromAfr',
                                    'China', 'US_EXtoAfr', 'US_IMfromAfr',
                                    'U.S.'], title='US-China Trade To Africa', template = 'plotly_dark')
tradeplot.write_html('CountryTrade.html')

# Trade Map: Routes, Ports including Protests Fig. 13
ports_df = pd.read_csv('ports_lat_long.csv',encoding = "ISO-8859-1")
geo_data = gpd.read_file('attributed_ports_updated.shx')
df = pd.read_csv('ports.csv',encoding = "ISO-8859-1")
merged = pd.concat([geo_data, df], axis=1)

gdf2 = gpd.GeoDataFrame(ports_df, geometry=gpd.points_from_xy(ports_df.Latitude,
                                                              ports_df.Longitude))
gdf2.columns=['port','lat','lng','loc']

trade_map = folium.Map(location=[0, 0], tiles="cartodbdark_matter", zoom_start=3)
file = 'data_maritime_route.geojson'

marker_cluster = MarkerCluster(name='Port popup', show=False)

#creating popup data along with plotting ports
for i in range(0,len(merged)):
    marker = folium.Marker([gdf2.iloc[i]['lat'],gdf2.iloc[i]['lng']])
    popup='Port:{}<br>Lat:{}<br>Long:{}<br>'.format(gdf2.iloc[i]['port'],gdf2.iloc[i]['lng'],gdf2.iloc[i]['lat'])
    folium.Popup(popup).add_to(marker)
    marker_cluster.add_child(marker)

#adding the ability to draw and export geojson files
draw = Draw(export=True,filename='data.geojson')
draw.add_to(trade_map)

#adding the maritime route geojson file
folium.GeoJson(json.load(open(file)),name='Maritime_route', show=False, style_function= lambda feature: {'color':'blue'}).add_to(trade_map)

folium.GeoJson(json.load(open('BCIM.txt')),name='Bangladesh-China-India-Myanmar Economic Corridor', show=False, style_function= lambda feature: {'color':'red'}).add_to(trade_map)

folium.GeoJson(json.load(open('CCAWEC.txt')),name='China-Central Asia-Western Asia Economic Corridor', show=False, style_function= lambda feature: {'color':'yellow'}).add_to(trade_map)

folium.GeoJson(json.load(open('CICPEC.txt')),name='China-Indochina Peninsula Economic Corridor', show=False, style_function= lambda feature: {'color':'white'}).add_to(trade_map)

folium.GeoJson(json.load(open('CMRECcompleted.txt')),name='China-Mongolia-Russia Economic Corridor, Completed', show=False, style_function= lambda feature: {'color':'purple'}).add_to(trade_map)

folium.GeoJson(json.load(open('CMRECplanned.txt')),name='China-Mongolia-Russia Economic Corridor, Planned', show=False,style_function= lambda feature: {'color':'green'}).add_to(trade_map)

folium.GeoJson(json.load(open('nelbec.txt')),name='New Eurasian Land Bridge Economic Corridor', show=False, style_function= lambda feature: {'color':'violet'}).add_to(trade_map)

folium.GeoJson(json.load(open('CPECcompleted.txt')),name='China-Pakistan Economic Corridor, Completed', show=False, style_function= lambda feature: {'color':'orange'}).add_to(trade_map)

folium.GeoJson(json.load(open('CPECplanned.txt')),name='China-Pakistan Economic Corridor, Planned', show=False, style_function= lambda feature: {'color':'brown'}).add_to(trade_map)


marker_cluster.add_to(trade_map)
folium.TileLayer('OpenStreetMap').add_to(trade_map)
folium.TileLayer('Stamen Terrain').add_to(trade_map)
folium.TileLayer('Stamentoner').add_to(trade_map)
folium.TileLayer('cartodbdark_matter').add_to(trade_map)
folium.LayerControl().add_to(trade_map)
############################################################################################################################################

### App ###
app = JupyterDash(__name__)

app.scripts.config.serve_locally = True
app.Title = "Belt and Road Initiative Study"

def serve_layout():
    return html.Div(className='row', children=[
        #Main title and figure 1
        html.Div([
            html.H1('Belt and Road Initiative Study', style={'textAlign': 'center','backgroundColor':'black', 'color': 'white', "text-decoration": "underline"}),
            html.Br(),
            html.Br(),
            html.Br()
        ]),
        html.Div([
            dcc.Graph(id='cntry_graph', figure=cntry_fig, style={'width':'99%'}),
            html.Br()
        ]),

        # media and visit figures figure 2, 3, 4
        html.Div(children=[
            html.H3('Diplomacy', style={'textAlign': 'center','backgroundColor':'black', 'color': 'white', "text-decoration": "underline"}),
            html.Br(),
            dcc.Graph(id="diplo_graph",figure=diplo_fig, style={'display': 'inline-block', 'width': '30%'}),
            dcc.Graph(id="media_graph",figure=media_fig, style={'display': 'inline-block', 'width': '30%'}),
            dcc.Graph(id="visit_graph",figure=visit_fig, style={'display': 'inline-block', 'width': '39%'}),
            html.Br()
        ]),

        # Figure 5 Inbound vs outbound chinese exchange students
        html.Div(children=[
            dcc.Graph(id='student_graph', figure = stud_fig, style={'display': 'inline-block', 'width': '99%'}),
            html.Br()
            #dcc.Graph(id='chn_invest_graph', figure = chn_investments_fig, style={'display': 'inline-block', 'width': '50%'})
        ]),

        # Coercive diplomatic action title (pending visuals)
        html.Div(children=[
            html.H5('Coercive Actions Against Foreign-Based Companies', style={'textAlign': 'center','backgroundColor':'black', 'color': 'white' }),
            dcc.Graph(id='action_graph', figure = compAction_fig, style={'display': 'inline-block', 'width': '54%'}),
            dcc.Graph(id='apology_graph', figure = compApol_fig, style={'display': 'inline-block', 'width': '45%'}),
            html.Br(),
            html.Br()
        ]),

        #Investments title & figures XX XX
        html.Div(children=[
            html.H3('Investments', style={'textAlign': 'center','backgroundColor':'black', 'color': 'white', "text-decoration": "underline"}),
            html.Br(),
            dcc.Graph(id='sectorbar_graph', figure = sectorbar, style={'display': 'inline-block', 'width': '54%'}),
            dcc.Graph(id='chn_invest_graph', figure = chn_investments_fig, style={'display': 'inline-block', 'width': '45%'})
        ]),

        #Number of Chinese investments & figures XX XX
        html.Div(children=[
            dcc.Graph(id='bri_investments_map', figure = mappy, style ={'display': 'inline-block', 'width': '55%'}),
            dcc.Graph(id="sunburst_chart",figure=burst, style={'display': 'inline-block', 'width': '44%'})
        ]),

        # Trade Line Chart US vs. China
        html.Div(children=[
            html.H3('International Trade', style={'textAlign': 'center','backgroundColor':'black', 'color': 'white', "text-decoration": "underline"}),
            html.Br(),
            dcc.Graph(id='trade_data', figure = tradeplot, style ={'display': 'inline-block', 'width': '99%'}),
            #dcc.Graph(id="bri_investments_percent",figure=percent10, style={'display': 'inline-block', 'width': '30%'})
        ]),

        #International trade ports and routes figure XX
        html.Div(children=[
            html.H5('Belt and Road Initiative Trade Map', style={'textAlign': 'center','backgroundColor':'black', 'color': 'white'}),
            html.Br(),
            #html.Iframe(id='trade_map', srcDoc= open('port_with_clusters.html', 'r').read(), width='95%', height="600", style={'border': 'none', "display": "inline-block"})
            html.Iframe(id='trade_map', srcDoc= open('port_with_clusters.html', 'r').read(), width='99%', height="900", style={'border': 'none', 'disply': 'flex', 'align-items': 'center', 'justify-content':'center'}),
            html.Br(),
            html.Br()
        ])
    ])

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server(debug=True)

############################################################################################################################################