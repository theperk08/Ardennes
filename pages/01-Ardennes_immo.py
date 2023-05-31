#  cd Documents\Wild_Code_School\Dojo_Immo
# streamlit run Ardennes_immo.py

import streamlit as st
import streamlit.components.v1 as components

st.header("Données du marché immobilier à Charleville-Mézières")

HtmlFile = open("Immo_08.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
components.html(source_code, width = 1000, height = 800)
