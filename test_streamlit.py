
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client

url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
zyte_api = st.secrets["zyte_api"]
zyte_api = '340150045b364ca5abcd6a44403b1835'
supabase: Client = create_client(url, key)

def get_odds_html(zyte_api, url):
    
    api_response = requests.post(
        "https://api.zyte.com/v1/extract",
        auth=(zyte_api, ""),
        json={
            "url": f"{url}/odds-comparison",
            "browserHtml": True,
        },
    )
    browser_html: str = api_response.json()["browserHtml"]
    
    return browser_html

def get_odds_data(browser_html):
    
    soup = BeautifulSoup(browser_html, 'html.parser')
    # Find all the divs containing horse runner information
    horse_rows = soup.find_all('div', attrs={'data-test-selector': 'RC-oddsRunnerContent__runnerRow'})

    # List to store all horses' bookmaker odds data
    all_odds_data = []

    # Iterate over each horse row
    for horse_row in horse_rows:
        # Extract the horse ID
        horse_id = horse_row['data-odds-horse-uid']
        # Loop through the elements containing odds information for each horse
        price_elements = horse_row.select('.RC-oddsRunnerContent__data')
        odds_dict = {}
        for price_element in price_elements:
            # Check if the required attributes are present
            if 'data-diffusion-bookmaker' in price_element.attrs:
                bookmaker = price_element['data-diffusion-bookmaker']
                odds_element = price_element.select_one('a', class_='RC-oddsRunnerContent__price')
                if odds_element['data-diffusion-decimal'] is None:
                    continue
                odds = float(odds_element['data-diffusion-decimal'])
                odds_dict[bookmaker] = odds
        # Add the horse ID to the odds data
        entry = {'horse_id': horse_id, **odds_dict}
        print(entry)
        all_odds_data.append(entry)
    df = pd.DataFrame(all_odds_data)
    return df



response_uk = supabase.table('uk_horse_racing').select('race_date','race_name', 'city', 'horse', 'jockey', 'odds_predicted', 'url', 'horse_id').execute()
response_uk = pd.DataFrame(response_uk.data)
odds_uk = get_odds_html(zyte_api, response_uk['url'][0])
odds_uk_df = get_odds_data(odds_uk)
uk_df = response_uk.merge(odds_uk_df, on='horse_id', how='left')
uk_df.drop(columns=['url', 'horse_id'], inplace=True)

response_fr = supabase.table('fr_horse_racing').select('race_date','race_name', 'city', 'horse', 'jockey', 'odds', 'odds_predicted').execute()
fr_df = pd.DataFrame(response_fr.data)


st.title('Horse Racing Data')
st.write('UK Horse Racing Data')
st.write(uk_df)
st.write('FR Horse Racing Data')
st.write(fr_df)


