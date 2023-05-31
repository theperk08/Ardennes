#  cd Documents\Wild_Code_School\Dojo_Immo
# streamlit run Ardennes_immo.py

import streamlit as st
import streamlit.components.v1 as components

# >>> import plotly.express as px
# >>> fig = px.box(range(10))
# >>> fig.write_html('test.html')

st.header("Données du marché immobilier à Charleville-Mézières")

HtmlFile = open("Immo_08.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
#print(source_code)
components.html(source_code)
