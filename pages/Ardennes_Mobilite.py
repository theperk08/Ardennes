import streamlit as st
import numpy as np
import pandas as pd
import json
import geopandas as gpd
import time

import plotly.express as px
import plotly.graph_objects as go
import matplotlib as plt
import requests
from geopy.distance import geodesic as GD

# cd Documents\Data_Analyse\Ardennes
# streamlit run Ardennes_mobilite_streamlit.py

#mapbox_access_token = open(".mapbox_token").read()

# BORNES
url_bornes = 'data_charleville_bornes_elec.csv'
df_bornes = pd.read_csv(url_bornes, sep=';')
df_bornes['lon'] = df_bornes['coordonneesXY'].apply(lambda x: x.split(',')[0][1:]).astype(float)
df_bornes['lat'] = df_bornes['coordonneesXY'].apply(lambda x: x.split(',')[1][:-1]).astype(float)
color_borne = 'green'

# PARKINGS VELOS
url_velos = 'data_charleville_parking_velo.csv'
df_velos = pd.read_csv(url_velos, sep=';')
df_velos['lon'] = df_velos['coordonneesxy'].apply(lambda x: x.split(',')[0][1:]).astype(float)
df_velos['lat'] = df_velos['coordonneesxy'].apply(lambda x: x.split(',')[1][:-1]).astype(float)
df_velos['capacite'].fillna(0, inplace = True)
color_velo = 'blue'

# BORNES CYCLAM
url_cyclam = 'data_charleville_parking_cyclam.csv'
df_cyclam = pd.read_csv(url_cyclam, sep=';')
# df_cyclam['lon'] = df_cyclam['position.longitude']
# df_cyclam['lat'] = df_cyclam['position.latitude']
#df_cyclam['capacite'].fillna(0, inplace = True)
color_cyclam = 'dodgerblue'

# ARRETS BUS
url = "data_charleville_bus.geojson"
df_bus = pd.DataFrame()
data = pd.read_json(url)
df_bus = pd.json_normalize(data['features'])
df_bus = df_bus[df_bus['geometry.type'] == 'Point']
df_bus['lon'] = df_bus['geometry.coordinates'].apply(lambda x: x[0])
df_bus['lat'] = df_bus['geometry.coordinates'].apply(lambda x : x[1])
df_bus = df_bus[~df_bus['properties.name'].isna()].reset_index()
color_bus = 'red'

# ADRESSES
df_adresses = pd.read_csv('Adresses_Charleville.csv.gz', sep = ';', compression = 'gzip')
liste_adresses = list(df_adresses['numero'].map(str) + df_adresses['rep'].map(str) + ' - ' + df_adresses['nom_voie'].map(str))

#hover1 = '<b>ok</b>'

def add_figure(fig1, fig2):
    for datas in fig2.data:
        fig1.add_trace(datas)
    return fig1


def add_point(lat, lon, size, color, text): #, hovertemp):
    point = go.Scattermapbox(lat = lat, lon = lon,
                             mode = 'markers',
                             marker = {'size': size, 'color': color},
                             text = text,
                             hoverinfo='text'
                            #hovertemplate = hovertemp
                            )
    fig.add_trace(point)
            
    
def distance_simple(lat1, long1, lat2, long2):
    """
    Calcul distance géographique entre deux points
    aux coordonnées en degrés décimaux
    
    """
    
    x = (lat2 - lat1)*np.cos((np.pi*(long1 + long2)/2)/180)
    y = long2 - long1
    z = np.sqrt(x**2 + y**2)
    k = 1.852 * 60 * 1000  # *1000 pour distance en mètres
    return k*z


def distances(point, liste):
    liste_distances = []
    for pts in liste:
        liste_distances += [distance_directe(point[0], point[1], pts[0], pts[1])]
    return liste_distances


def liste_proches(lat_depart, lon_depart, data, nombre, attribut):
    """
    pour rechercher la liste des 'nombre' points les plus proches
    à vol d'oiseau à partir d'un point de départ (lat_depart, lon_depar)
    """
    
    
    liste_distances = pd.DataFrame(columns = ['index', 'lat', 'lon', 'distance', 'nom'])
    print(liste_distances)
    
    for index, row in data.iterrows():
        
        lat_2 = data.loc[index, 'lat']
        lon_2 = data.loc[index, 'lon']
        nom = data.loc[index, attribut]        
        
        #liste_distances = pd.concat([liste_distances, pd.DataFrame({ 'lat' : lat_2, 'lon' : lon_2, 'distance' : distance_simple(lat_depart, lon_depart, lat_2, lon_2), 'nom' : nom}, index= [index])])
        liste_distances = pd.concat([liste_distances, pd.DataFrame({ 'lat' : lat_2, 'lon' : lon_2, 'distance' : GD((lat_depart, lon_depart), (lat_2, lon_2)).m, 'nom' : nom}, index= [index])])  
    
    liste_distances = liste_distances.sort_values(by = 'distance').head(nombre)
    
    return liste_distances

def distance_api_geo(lat_depart, lon_depart, data):
    """
    Calcul distance style Manhattan (piétonne)
    à l'aide de l'API Géoportail
    """
    
    velo_dist = pd.DataFrame(columns = ['lat', 'lon', 'nom', 'distance'])
    
    for index, row in enumerate(data.itertuples(), 1):
        print(index)
        print(row)
        lat_velo1 = row.lat
        lon_velo1 = row.lon
        nom_velo1 = row.nom   

        print(f"https://data.geopf.fr/navigation/itineraire?resource=bdtopo-osrm&profile=pedestrian&optimization=shortest&start={lon_depart},{lat_depart}&end={lon_velo1},{lat_velo1}&intermediates=&constraints=&geometryFormat=polyline&getSteps=true&getBbox=true")
        
        # r = requests.get(f"https://wxs.ign.fr/calcul/geoportail/itineraire/rest/1.0.0/route?resource=bdtopo-osrm&profile=pedestrian&optimization=shortest&start={lon_depart},{lat_depart}&end={lon_velo1},{lat_velo1}&intermediates=&constraints=&geometryFormat=polyline&getSteps=true&getBbox=true")
        r = requests.get(f"https://data.geopf.fr/navigation/itineraire?resource=bdtopo-osrm&profile=pedestrian&optimization=shortest&start={lon_depart},{lat_depart}&end={lon_velo1},{lat_velo1}&intermediates=&constraints=&geometryFormat=polyline&getSteps=true&getBbox=true")
        
        print(r.content)
        routes = json.loads(r.content)
        distance = routes['distance']
        velo_dist = pd.concat([velo_dist, pd.DataFrame({'lat' : lat_velo1, 'lon' : lon_velo1, 'nom' : nom_velo1, 'distance' : distance}, index = [index])])
    
    velo_dist = velo_dist.sort_values(by = 'distance')
            
    return velo_dist

# FIGURES
fig = go.Figure()

## BORNES
bornes_lat = df_bornes.lat
bornes_lon = df_bornes.lon
locations_bornes_name = df_bornes.nom_station
hover_bornes = 'Borne recharge auto' + '<br>' + locations_bornes_name + '<br>' + bornes_lat.map(lambda x : str(round(x, 4)) + 'N') + ' - ' + bornes_lon.map(lambda x : str(round(x, 4)) + 'E')

fig_bornes = add_point(bornes_lat, bornes_lon, 10,  color_borne, hover_bornes) #, hover1)

## VELOS
velos_lat = df_velos.lat
velos_lon = df_velos.lon
locations_velos_name = df_velos.mobilier
hover_velos = 'Parking vélo' + '<br>' + locations_velos_name + '<br>' + velos_lat.map(lambda x : str(round(x, 4)) + 'N') + ' - ' + velos_lon.map(lambda x : str(round(x, 4)) + 'E')

fig_velos = add_point(velos_lat, velos_lon, 10, color_velo, hover_velos) #, hover1)

## CYCLAM
cyclam_lat = df_cyclam.lat
cyclam_lon = df_cyclam.lon
locations_cyclam_name = df_cyclam.name
hover_velos = 'Station Cyclam' + '<br>' + locations_cyclam_name + '<br>' + cyclam_lat.map(lambda x : str(round(x, 4)) + 'N') + ' - ' + cyclam_lon.map(lambda x : str(round(x, 4)) + 'E')

fig_cyclam = add_point(cyclam_lat, cyclam_lon, 10, color_cyclam, hover_velos) #, hover1)



## BUS
bus_lat = df_bus.lat
bus_lon = df_bus.lon
locations_bus_name = df_bus['properties.name']
hover_bus = 'Arrêt de bus' + '<br>' + locations_bus_name + '<br>' + bus_lat.map(lambda x : str(round(x, 4)) + 'N') + ' - ' + bus_lon.map(lambda x : str(round(x, 4)) + 'E')

fig_bus = add_point(bus_lat, bus_lon, 10, color_bus, hover_bus) #, hover1)



col1, col2, col3 = st.columns(3)
with col2:
    st.markdown('<h4><center>Vous habitez ou vous vous rendez à <b>Charleville-Mézières</b></center></h4>', unsafe_allow_html = True)
    st.markdown('<h4><center>et vous souhaiteriez connaître les points de mobilité</center></h4>', unsafe_allow_html = True)
    st.markdown("<center>(<span style='color:{velo};'>parking vélo</span>, <a href = 'https://cyclam.ecovelo.mobi/#/home' target='_blank'  style='color:{cyclam};'>station cyclam</a>, <a href='https://www.bustac.fr/' target ='_blank' style='color:{bus};'>arrêt de bus</a>, <span style='color:{borne};'>borne de recharge électrique auto</span>)</center>".format(velo=color_velo, cyclam=color_cyclam, bus=color_bus, borne=color_borne), unsafe_allow_html = True)
    st.markdown("<h4><center>les plus proches : <span style='color:purple;'>entrez une adresse...</span></center></h4>", unsafe_allow_html = True)

    with st.form('form_1'):
        adresse = st.selectbox("Adresse à Charleville-Mézières : ",
                               liste_adresses)
        num_adresse = '0'
        voie_adresse = 'inconnue'
        try:
            num_adresse = adresse.split(' - ')[0]
            voie_adresse = adresse.split(' - ')[1]
        except:
            st.write('Problème avec adresse !')

        submit1 = st.form_submit_button("OK !")    

if submit1:
    
    cols1, cols2 = st.columns([1, 2]) # colonnes proportionnelles à la liste des nombres
    
    # ADRESSE CHOISIE
    adr_choisie = df_adresses.iloc[liste_adresses.index(adresse): liste_adresses.index(adresse) + 1,:]
    
    lat = adr_choisie['lat']
    lon = adr_choisie['lon']
    
    lat_1 = adr_choisie.loc[liste_adresses.index(adresse),'lat']
    lon_1 = adr_choisie.loc[liste_adresses.index(adresse),'lon']
    
    ## marquage du point adresse   
    add_point(lat, lon,20, 'purple', f'<span style ="color:purple">Adresse :<br> {adresse}</span>') #, hover1)
    add_point(lat, lon, 8, 'yellow', f'<span style ="color:purple">Adresse :<br> {adresse}</span>') #, hover1)    
    
    with cols1:
        for k in range(10):
            st.write(' ')
        st.write("**:violet[Pour l'adresse : {} {}]**".format(num_adresse, voie_adresse))
        st.write(f'**:violet[lat = {str(round(lat_1,4))} ; lon = {str(round(lon_1, 4))}]**')

        # VELOS
        nombre_velos = 5
        liste_distances_velos = liste_proches(lat_1, lon_1, df_velos, nombre_velos, 'mobilier')    

        velo = distance_api_geo(lat_1, lon_1, liste_distances_velos)    

        for i in range(1):
            lat_velo1 = velo.iloc[i: i + 1, :].lat
            lon_velo1 = velo.iloc[i: i + 1, :].lon
            nom_velo1 = "<span style ='color:{velo}'>Parking vélo<br>".format(velo=color_velo) + velo.iloc[i: i + 1, :].nom + "<br> à " + str(round(velo.iloc[i]["distance"])) + ' mètres</span>'

            add_point(lat_velo1, lon_velo1, 20, color_velo, nom_velo1) # , hover1)
            add_point(lat_velo1, lon_velo1, 8, 'yellow', nom_velo1) #, hover1)
        st.markdown('<span style ="color:{velo}">Parking vélo le plus proche ({nom}) à {distance} mètres'.format(velo=color_velo, nom = velo.iloc[0]['nom'], distance = velo.iloc[0]['distance']), unsafe_allow_html = True)
        
        
        # CYCLAM       
        nombre_velos = 5
        liste_distances_velos = liste_proches(lat_1, lon_1, df_cyclam, nombre_velos, 'name')    

        # limite de 5 requetes/seconde pour l'api geopf
        time.sleep(1)
        velo = distance_api_geo(lat_1, lon_1, liste_distances_velos)    

        for i in range(1):
            lat_velo1 = velo.iloc[i: i + 1, :].lat
            lon_velo1 = velo.iloc[i: i + 1, :].lon
            nom_velo1 = "<span style ='color:{cyclam}'>Station cyclam<br>".format(cyclam=color_cyclam) + velo.iloc[i: i + 1, :].nom + "<br> à " + str(round(velo.iloc[i]["distance"])) + ' mètres</span>'

            add_point(lat_velo1, lon_velo1, 20, color_cyclam, nom_velo1) # , hover1)
            add_point(lat_velo1, lon_velo1, 8, 'yellow', nom_velo1) #, hover1)

        st.markdown("<span style ='color:{cyclam}'>Station cyclam la plus proche ({nom}) à {distance} mètres".format(cyclam=color_cyclam, nom = velo.iloc[0]['nom'], distance = velo.iloc[0]['distance']), unsafe_allow_html = True)

       
        
        
        # BUS

        nombre_bus = 5
        liste_distances_bus = liste_proches(lat_1, lon_1, df_bus, nombre_bus, 'properties.name')   

        # limite de 5 requetes/seconde pour l'api geopf
        time.sleep(1)
        bus = distance_api_geo(lat_1, lon_1, liste_distances_bus)

        for i in range(1):        

            lat_bus1 = bus.iloc[i: i + 1, :].lat
            lon_bus1 = bus.iloc[i: i + 1, :].lon
            nom_bus1 = "<span style ='color:{bus}'>Arrêt de bus<br>".format(bus=color_bus) + bus.iloc[i: i + 1, :].nom + "<br> à " + str(round(bus.iloc[i]["distance"])) + ' mètres</span>'

            add_point(lat_bus1, lon_bus1, 20, color_bus, nom_bus1) #, hover1)
            add_point(lat_bus1, lon_bus1, 8, 'yellow', nom_bus1) #, hover1)    

        st.markdown("<span style ='color:{bus}'>Arrêt de bus le plus proche ({nom}) à {distance} mètres".format(bus=color_bus, nom = bus.iloc[0]['nom'], distance = bus.iloc[0]['distance']),unsafe_allow_html = True) 

        # BORNES ELECTRIQUES

        nombre_bornes = 5
        liste_distances_bornes = liste_proches(lat_1, lon_1, df_bornes, nombre_bornes, 'nom_station')

        #st.write('bornes')
        #st.write(liste_distances_bornes)

        # limite de 5 requetes/seconde pour l'api geopf
        time.sleep(1)
        
        borne = distance_api_geo(lat_1, lon_1, liste_distances_bornes)
        print('bornes')
        print(borne)

        for i in range(1):
            lat_borne1 = borne.iloc[i: i + 1, :].lat
            lon_borne1 = borne.iloc[i: i + 1, :].lon
            nom_borne1 = "<span style ='color:{borne}'>Borne électrique auto<br>".format(borne=color_borne) + str(borne.iloc[i]['nom']) + "<br> à " + str(round(borne.iloc[i]["distance"])) + ' mètres</span>'     

            add_point(lat_borne1, lon_borne1, 20, color_borne, nom_borne1) #, hover1)
            add_point(lat_borne1, lon_borne1, 8, 'yellow', nom_borne1) #, hover1)    

        st.markdown("<span style ='color:{borne}'>Borne auto de recharge la plus proche ({nom}) à {distance} mètres".format(borne=color_borne, nom = borne.iloc[0]['nom'], distance = borne.iloc[0]['distance']), unsafe_allow_html = True)


        # FIGURE TOTALE

        fig.update_layout(
        #title='Bornes, vélos, bus',
        title = dict({'text':'<span style="color:{velo};">Parkings vélos</span> + <span style="color:{cyclam};">Stations cyclam</span> + <span style="color:{bus};">Arrêts bus</span> + <span style="color:{borne};">Bornes autos électriques</span>'.format(velo=color_velo, cyclam=color_cyclam, bus=color_bus, borne=color_borne),
                                     'x' : 0.2}),
        autosize=True,
        hovermode='closest',
        showlegend=False,
        mapbox=dict(
            #accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat = lat_1,
                lon = lon_1
            ),
            pitch=0,
            zoom=14.5,
            style= 'open-street-map' #'outdoors'
        ),
        width = 700,
        height = 700
        )
    
    ## Affichage de la figure
    with cols2:
        st.plotly_chart(fig)
    
    
    if False:
        r = requests.get(f"http://router.project-osrm.org/route/v1/car/{lon_1},{lat_1};{lon_2},{lat_2}?geometries=geojson&overview=false""")
        routes = json.loads(r.content)
        route_1 = routes.get("routes")[0]
        distance = route_1['distance']
        distances += [distance]
        if distance < distance_mini:
            distance_mini = distance
            velo = df_velos.iloc[index]
            
    
        st.write(f'distance mini = {distance_mini} mètres')
        st.write('avec arrêt bus : ')
        st.write(velo)
    
    
        
