import models
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas_datareader.data as pdr
import yfinance as yfin
yfin.pdr_override()

SQLALCHEMY_DATABASE_URL = "postgresql://wizard_app:password@localhost:5432/wizards_database"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Session = sessionmaker(bind=engine)


def main():
    start = datetime(2022, 7, 7)
    end = datetime(2023, 7, 7)

    session = Session()
    tickers = session.query(models.TickerMaster.ticker).all()

    for ticker in tickers:
        try:
            df = pdr.get_data_yahoo(ticker[0], start, end)
            for index, row in df.iterrows():
                close_price = row['Close']
                print(f"{ticker[0]}:{index}: {close_price}")
                ticker_price = models.TickerPrice(
                    ticker=ticker.ticker, date=index, price=close_price)
                session.add(ticker_price)
        except Exception as e:
            print(f"Error: {e}")
            continue

    session.commit()


if __name__ == '__main__':
    main()
