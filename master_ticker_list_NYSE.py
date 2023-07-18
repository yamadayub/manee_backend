import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import models

SQLALCHEMY_DATABASE_URL = "postgresql://wizard_app:password@localhost:5432/wizards_database"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def get_tickers(url):
    print(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    div = soup.find('div', attrs={'id': 'ctl00_cph1_divSymbols'})
    table = div.find('table')
    rows = table.find_all('tr')[1:]

    tickers = []
    for row in rows:
        ticker = row.find_all('td')[0].find('a').text
        tickers.append(ticker)

    return tickers


def main():
    base_url = 'https://eoddata.com/stocklist/NYSE/'
    initials = [chr(i) for i in range(ord('A'), ord('Z')+1)]
    urls = [f'{base_url}{initial}.htm' for initial in initials]
    session = Session()

    for url in urls:
        tickers = get_tickers(url)

        for ticker in tickers:
            master_ticker = models.TickerMaster(ticker=ticker)
            master_ticker.exchange = "NYSE"
            session.add(master_ticker)

    session.commit()


if __name__ == '__main__':
    main()
