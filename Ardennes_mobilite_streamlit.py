import streamlit as st

# DEBUT PAGE STREAMLIT

pages = [st.Page('pages/Ardennes_Mobilite.py', title = '🚲 Mobilité Charleville'),
         st.Page('pages/Ardennes_immo.py', title = '🏠 Ardennes Immo')
         ]
  

pg = st.navigation(pages)
pg.run()