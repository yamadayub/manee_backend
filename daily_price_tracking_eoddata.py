import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import models
from datetime import datetime, timedelta
import time

SQLALCHEMY_DATABASE_URL = "postgresql://wizard_app:password@localhost:5432/wizards_database"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


def get_tickers_from_db(initial):
    # URLから対象となるイニシャルで始まるtickerのリストをticker_masterから取得
    session = Session()
    tickers = session.query(models.TickerMaster.ticker).filter(
        models.TickerMaster.ticker.like(f"{initial}%")).all()
    session.close()
    tickers = [t[0] for t in tickers]
    return tickers


def get_tickers_price_with_date(url, tickers):
    print(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # ticker, date, priceのlistを返却する
    tickers_price_with_date = []

    div = soup.find('div', attrs={'id': 'ctl00_cph1_divSymbols'})
    table = div.find('table')
    rows = table.find_all('tr')[1:]

    for row in rows:
        ticker = row.find_all('td')[0].find('a').text
        if ticker in tickers:
            tds = row.find_all('td')
            date = datetime.now().date() - timedelta(days=1)
            price = round(float(tds[4].text.strip().replace(',', '')), 2)
            tickers_price_with_date.append(
                {'ticker': ticker, 'date': date, 'price': price})

    return tickers_price_with_date


def main():
    base_url = 'https://eoddata.com/stocklist/NYSE/'
    initials = [chr(i) for i in range(ord('A'), ord('Z')+1)]
    urls = [f'{base_url}{initial}.htm' for initial in initials]

    session = Session()
    for url in urls:
        initial = url.split('/')[-1].split('.')[0]
        target_tickers = get_tickers_from_db(initial)
        tickers_result = get_tickers_price_with_date(url, target_tickers)

        for ticker_result in tickers_result:
            ticker_price = models.TickerPrice(
                ticker=ticker_result['ticker'], date=ticker_result['date'], price=ticker_result['price'])
            session.add(ticker_price)
        print(f"Finished scraping data from {url}")
        time.sleep(30)  # 30s待機
    session.commit()


if __name__ == '__main__':
    main()
