import streamlit as st
import numpy as np
import pandas as pd
import json
import geopandas as gpd

import plotly.express as px
import plotly.graph_objects as go
import matplotlib as plt
import requests

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
        
        liste_distances = pd.concat([liste_distances, pd.DataFrame({ 'lat' : lat_2, 'lon' : lon_2, 'distance' : distance_simple(lat_depart, lon_depart, lat_2, lon_2), 'nom' : nom}, index= [index])])
                  
    
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
        
        r = requests.get(f"https://wxs.ign.fr/calcul/geoportail/itineraire/rest/1.0.0/route?resource=bdtopo-osrm&profile=pedestrian&optimization=shortest&start={lon_depart},{lat_depart}&end={lon_velo1},{lat_velo1}&intermediates=&constraints=&geometryFormat=polyline&getSteps=true&getBbox=true")
        routes = json.loads(r.content)
        distance = routes['distance']
        velo_dist = pdconcat([velo_dist, pd.DataFrame({'lat' : lat_velo1, 'lon' : lon_velo1, 'nom' : nom_velo1, 'distance' : distance}, index = [index])
                              
    velo_dist = velo_dist.sort_values(by = 'distance')
            
    return velo_dist

# FIGURES
fig = go.Figure()

## BORNES
bornes_lat = df_bornes.lat
bornes_lon = df_bornes.lon
locations_bornes_name = df_bornes.nom_station
hover_bornes = locations_bornes_name + '<br>' + bornes_lat.map(lambda x : str(round(x, 4)) + 'N') + ' - ' + bornes_lon.map(lambda x : str(round(x, 4)) + 'E')

fig_bornes = add_point(bornes_lat, bornes_lon, 10, 'black', hover_bornes) #, hover1)

## VELOS
velos_lat = df_velos.lat
velos_lon = df_velos.lon
locations_velos_name = df_velos.mobilier
hover_velos = locations_velos_name + '<br>' + velos_lat.map(lambda x : str(round(x, 4)) + 'N') + ' - ' + velos_lon.map(lambda x : str(round(x, 4)) + 'E')

fig_velos = add_point(velos_lat, velos_lon, 10, 'blue', hover_velos) #, hover1)

## BUS
bus_lat = df_bus.lat
bus_lon = df_bus.lon
locations_bus_name = df_bus['properties.name']
hover_bus = locations_bus_name + '<br>' + bus_lat.map(lambda x : str(round(x, 4)) + 'N') + ' - ' + bus_lon.map(lambda x : str(round(x, 4)) + 'E')

fig_bus = add_point(bus_lat, bus_lon, 10, 'red', hover_bus) #, hover1)


# DEBUT PAGE STREAMLIT
st.set_page_config(
    page_title = "Ardennes Mobilité",
    layout = "wide",
    page_icon = "🚲")



col1, col2, col3 = st.columns(3)
with col2:
    st.markdown('Vous habitez ou vous vous rendez à **Charleville-Mézières**')
    st.markdown('et vous souhaiteriez connaître les points de mobilité')
    st.markdown('(**:blue[parking vélo], :red[arrêt de bus], :green[borne de recharge électrique auto]**)')
    st.markdown('les plus proches : **:violet[entrez une adresse...]**')

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
    
    # ADRESSE CHOISIE
    adr_choisie = df_adresses.iloc[liste_adresses.index(adresse): liste_adresses.index(adresse) + 1,:]
    
    lat = adr_choisie['lat']
    lon = adr_choisie['lon']
    
    lat_1 = adr_choisie.loc[liste_adresses.index(adresse),'lat']
    lon_1 = adr_choisie.loc[liste_adresses.index(adresse),'lon']
    
    ## marquage du point adresse   
    add_point(lat, lon,20, 'purple', f'<span style ="color:purple">Adresse :<br> {adresse}</span>') #, hover1)
    add_point(lat, lon, 8, 'yellow', f'<span style ="color:purple">Adresse :<br> {adresse}</span>') #, hover1)    
       
    st.write("**:violet[Pour l'adresse : {} {}]**".format(num_adresse, voie_adresse))
    st.write(f'**:violet[lat = {str(round(lat_1,4))} ; lon = {str(round(lon_1, 4))}]**')
    
    # VELOS
    nombre_velos = 6
    liste_distances_velos = liste_proches(lat_1, lon_1, df_velos, nombre_velos, 'mobilier')    
       
    velo = distance_api_geo(lat_1, lon_1, liste_distances_velos)    
    
    for i in range(3):
        lat_velo1 = velo.iloc[i: i + 1, :].lat
        lon_velo1 = velo.iloc[i: i + 1, :].lon
        nom_velo1 = "<span style ='color:blue'>Parking vélo<br>" + velo.iloc[i: i + 1, :].nom + "<br> à " + str(round(velo.iloc[i]["distance"])) + ' mètres</span>'
        
        add_point(lat_velo1, lon_velo1, 20, color_velo, nom_velo1) # , hover1)
        add_point(lat_velo1, lon_velo1, 8, 'yellow', nom_velo1) #, hover1)
    
    st.write(f'**:blue[Parking vélo le plus proche ({velo.iloc[0]["nom"]}) à {velo.iloc[0]["distance"]} mètres]**')
    
    # BUS
    
    nombre_bus = 6
    liste_distances_bus = liste_proches(lat_1, lon_1, df_bus, nombre_bus, 'properties.name')   
   
    bus = distance_api_geo(lat_1, lon_1, liste_distances_bus)
    
    for i in range(3):        
        
        lat_bus1 = bus.iloc[i: i + 1, :].lat
        lon_bus1 = bus.iloc[i: i + 1, :].lon
        nom_bus1 = "<span style ='color:red'>Arrêt de bus<br>" + bus.iloc[i: i + 1, :].nom + "<br> à " + str(round(bus.iloc[i]["distance"])) + ' mètres</span>'
        
        add_point(lat_bus1, lon_bus1, 20, color_bus, nom_bus1) #, hover1)
        add_point(lat_bus1, lon_bus1, 8, 'yellow', nom_bus1) #, hover1)    
    
    st.write(f'**:red[Arrêt de bus le plus proche ({bus.iloc[0]["nom"]}) à {bus.iloc[0]["distance"]} mètres]**')
    
    # BORNES ELECTRIQUES
    
    nombre_bornes = 6
    liste_distances_bornes = liste_proches(lat_1, lon_1, df_bornes, nombre_bornes, 'nom_station')
    
    #st.write('bornes')
    #st.write(liste_distances_bornes)
    
    borne = distance_api_geo(lat_1, lon_1, liste_distances_bornes)
    print('bornes')
    print(borne)
   
    for i in range(3):
        lat_borne1 = borne.iloc[i: i + 1, :].lat
        lon_borne1 = borne.iloc[i: i + 1, :].lon
        nom_borne1 = "<span style ='color:green'>Borne électrique auto<br>" + str(borne.iloc[i]['nom']) + "<br> à " + str(round(borne.iloc[i]["distance"])) + ' mètres</span>'     
        
        add_point(lat_borne1, lon_borne1, 20, color_borne, nom_borne1) #, hover1)
        add_point(lat_borne1, lon_borne1, 8, 'yellow', nom_borne1) #, hover1)    
        
    st.markdown(f'**:green[Borne auto de recharge la plus proche ({borne.iloc[0]["nom"]}) à {borne.iloc[0]["distance"]} mètres]**')
                
        
    # FIGURE TOTALE
    
    fig.update_layout(
    #title='Bornes, vélos, bus',
    title = dict({'text':'<span style="color:blue;">Parkings vélos</span> + <span style="color:red;">Arrêts bus</span> + <span style="color:green;">Bornes autos électriques</span>',
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
        style='open-street-map' #'outdoors'
    ),
    width = 800,
    height = 800
    )
    
    ## Affichage de la figure
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
    
    
        
