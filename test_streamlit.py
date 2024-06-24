import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
import time
from supabase import create_client, Client

url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
zyte_api = st.secrets["zyte_api"]
supabase: Client = create_client(url, key)


def get_odds_html(url):
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")

    # Initialize Firefox driver
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)
    try:
        url = f'{url}/odds-comparison'
        driver.get(url)
        time.sleep(5)  # Let the page load
        
        browser_html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(browser_html, 'html.parser')

        horse_rows = soup.find_all('div', attrs={'data-test-selector': 'RC-oddsRunnerContent__runnerRow'})
        all_odds_data = []

        for horse_row in horse_rows:
            horse_id = horse_row['data-odds-horse-uid']
            price_elements = horse_row.select('.RC-oddsRunnerContent__data')
            odds_dict = {}
            for price_element in price_elements:
                if 'data-diffusion-bookmaker' in price_element.attrs:
                    bookmaker = price_element['data-diffusion-bookmaker']
                    odds_element = price_element.select_one('a.RC-oddsRunnerContent__price')
                    odds = float(odds_element['data-diffusion-decimal']) if odds_element.get('data-diffusion-decimal') else 0.0
                    odds_dict[bookmaker] = odds

            entry = {'horse_id': horse_id, **odds_dict}
            all_odds_data.append(entry)
        
        df = pd.DataFrame(all_odds_data)
        df['horse_id'] = df['horse_id'].astype(int)
    except Exception as e:
        driver.quit()
        print(e)
        raise e
    return df

def get_data_uk():
    response_uk = supabase.table('uk_horse_racing').select('race_date','race_name', 'city', 'horse', 'jockey', 'odds_predicted', 'url', 'horse_id').execute()
    response_uk = pd.DataFrame(response_uk.data)
    url = response_uk['url'].values[0]
    return url, response_uk

def main():
    st.title("Horse Racing Odds Prediction")
    url, response_uk = get_data_uk()
    response_uk_pre = response_uk[['horse_id','race_date', 'race_name', 'city', 'horse', 'jockey', 'odds_predicted']]
    # Create a placeholder for the dataframe
    df_placeholder = st.empty()

    # Display the initial dataframe
    df_placeholder.dataframe(response_uk_pre)

    if st.button("Fetch Odds"):
        with st.spinner("Fetching data..."):
            odds_df = get_odds_html(url)
            if odds_df.empty:
                st.error("Error fetching odds data")
                return
            final_df = pd.merge(response_uk, odds_df, on='horse_id', how='left')
            final_df.drop(columns=['horse_id', 'url'], inplace=True)
            df_placeholder.dataframe(final_df)

if __name__ == "__main__":
    main()



