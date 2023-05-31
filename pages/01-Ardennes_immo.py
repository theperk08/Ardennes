#  cd Documents\Wild_Code_School\Dojo_Immo
# streamlit run Ardennes_immo.py

# [source et exemples d'utilisation](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/?reuses_page=6#/community-reuses)
# [data](https://files.data.gouv.fr/geo-dvf/latest/csv/)

import streamlit as st
import numpy as np
import pandas as pd
import json
import geopandas as gpd

import plotly.express as px
import plotly.graph_objects as go
import matplotlib as plt
import requests


#Call et concat l'ensemble des data set
data_list =[]

for year in range (2018,2023) :
    df = pd.read_csv('https://files.data.gouv.fr/geo-dvf/latest/csv/%s/communes/08/08105.csv'% year, sep=",")
    data_list.append(df)

df = pd.concat(data_list)
def api(df):
    #Convert date time
    df["date_mutation"] = pd.to_datetime(df["date_mutation"])
    #Create colone year
    df["year"] = df["date_mutation"].dt.year
    #Rempli les cell vides
    df[['lot1_surface_carrez','lot2_surface_carrez','lot3_surface_carrez','lot4_surface_carrez','lot5_surface_carrez']] = df[['lot1_surface_carrez','lot2_surface_carrez','lot3_surface_carrez','lot4_surface_carrez','lot5_surface_carrez']].fillna(0)
    #Additionne et regroupe les surface carrez en une colone
    df["surface_carrez"] = df['lot1_surface_carrez'] + df['lot2_surface_carrez']+df['lot3_surface_carrez']+df['lot4_surface_carrez']+df['lot5_surface_carrez']
    #Supprime les colones inutiles
    df.drop(columns ={'numero_disposition','code_departement','ancien_nom_commune','code_commune',"nom_commune",'code_departement',"ancien_code_commune",'ancien_id_parcelle','numero_volume','numero_volume','lot1_numero','lot1_surface_carrez','lot2_numero','lot2_surface_carrez','lot3_numero','lot3_surface_carrez','lot4_numero','lot4_surface_carrez','lot5_numero','lot5_surface_carrez','code_nature_culture_speciale','code_nature_culture','nature_culture_speciale'}, inplace =True)

api(df)


df_geo = gpd.read_file("cadastre-08105-parcelles.json")
# df_geo


df_appart = df[df["type_local"] == "Appartement"]

#id_parc = '08105000AP0180'
#id_parc = '08105000AB0380'
#print(df_appart[df_appart['id_parcelle'] == id_parc])

#id_mut = '2021-104985'
#print(df_appart[df_appart['id_mutation'] == id_mut])


#Group les biens par id prend le premier prix et additionne les surfaces 
df_appart_mean = df_appart.groupby('id_mutation').agg({
    'valeur_fonciere' : 'first',
    'surface_reelle_bati' : 'first',
    'date_mutation' : 'first',
    'nature_mutation' : 'first',
    'id_parcelle' : 'first',
    'year' : 'first'
    }).reset_index()

#id_parc = '08105000AP0180'
#id_parc = '08105000AB0380'
#print(df_appart_mean[df_appart_mean['id_parcelle'] == id_parc])

#Prix du m2 appartement 
df_appart_mean["Prix_m2"] = df_appart_mean["valeur_fonciere"] / df_appart_mean["surface_reelle_bati"]
#Supprime les doublons en groupant les adresse
df_appart_mean = df_appart_mean.groupby('id_parcelle').agg({
    'Prix_m2': "mean",
    'id_mutation' : 'first',
    'date_mutation' : 'first',
    'nature_mutation' : 'first',
    'year' : 'first'
    }).reset_index()

df_appart_mean = df_appart_mean.sort_values(by = 'year')


df_maison = df[df["type_local"] == "Maison"]


#Group les biens par id prend le premier prix et additionne les surfaces 
df_maison_mean = df_maison.groupby('id_mutation').agg({
    'valeur_fonciere' : 'first',
    'surface_reelle_bati' : 'first',
    'date_mutation' : 'first',
    'nature_mutation' : 'first',
    'id_parcelle' : 'first',
    'adresse_nom_voie' : 'first',
    'longitude' :'first',
    'latitude' : 'first'
    }).reset_index()



#Prix du m2 appartement 
df_maison_mean["Prix_m2"] = df_maison_mean["valeur_fonciere"] / df_maison_mean["surface_reelle_bati"]
#Supprime les doublons en groupant les adresse
df_maison_mean = df_maison_mean.groupby('id_parcelle').agg({
    'Prix_m2': "mean",
    'id_mutation' : 'first',
    'date_mutation' : 'first',
    'nature_mutation' : 'first',
    'adresse_nom_voie' : 'first',
    'longitude' :'first',
    'latitude' : 'first'
    }).reset_index()

df_maison_mean = df_maison_mean.loc[(df_maison_mean["Prix_m2"] > 100) & (df_maison_mean["Prix_m2"] < 6000) ]


df_visu = df_appart_mean

fig_prix_moyen_appart = px.choropleth_mapbox(df_visu,
                           geojson=df_geo, 
                           color=df_visu.Prix_m2,
                           locations=df_visu.id_parcelle, 
                           range_color = [0, 3000],
                           featureidkey="properties.id", # nom de colonne du fichier geojson qui fera le lien avec le data frame
                                                           # par sécurité il vaut mieux que le dataframe et le geojson aient un nom de colonne identique comme clé
                                                           # donc j'aurais mieux fait de recréer une colonne nom dans le dataframe
                           center={"lat": 49.76, "lon": 4.725},
                           mapbox_style="carto-positron",
                           zoom=12.5,
                           width=1200, height=900
                          )
fig_prix_moyen_appart.update_layout(title = dict({'text':'Prix au m² des appartements', 'x' : 0.5, 'xanchor': 'center'}))
# fig_prix_moyen_appart.show()


st.plotly_chart(fig_prix_moyen_appart)