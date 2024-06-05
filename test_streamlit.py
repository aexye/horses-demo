
import streamlit as st
import pandas as pd

from supabase import create_client, Client

url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

response_uk = supabase.table('uk_horse_racing').select('race_date','race_name', 'city', 'horse', 'jockey', 'odds', 'odds_predicted').execute()
response_fr = supabase.table('fr_horse_racing').select('race_date','race_name', 'city', 'horse', 'jockey', 'odds', 'odds_predicted').execute()

st.title('Horse Racing Data')
st.write('UK Horse Racing Data')
st.write(pd.DataFrame(response_uk.data))
st.write('FR Horse Racing Data')
st.write(pd.DataFrame(response_fr.data))
