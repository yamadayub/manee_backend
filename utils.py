from database import SessionLocal
import models
from decimal import Decimal
import datetime as _dt
import schemas
from sqlalchemy import and_
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy.orm import contains_eager


def setGrowth(portfolio: models.Portfolio):
    session = SessionLocal()

    # ポートフォリオに属するtickerの2022年度末の価格を取得
    end_of_2022_prices = []
    for ticker in portfolio.tickers:
        stmt = session.query(models.TickerPrice.price).filter_by(ticker=ticker.ticker).filter(models.TickerPrice.date >=
                                                                                              '2022-01-01').filter(models.TickerPrice.date <= '2022-12-31').order_by(models.TickerPrice.date.desc()).first()
        price = stmt[0] if stmt is not None else 0
        end_of_2022_prices.append(
            Decimal(str(price)) * Decimal(str(ticker.ratio)))

    # ポートフォリオに属するtickerの最新価格を取得
    latest_prices = []
    for ticker in portfolio.tickers:
        stmt = session.query(models.TickerPrice.price).filter_by(
            ticker=ticker.ticker).order_by(models.TickerPrice.date.desc()).first()
        price = stmt[0] if stmt is not None else 0
        latest_prices.append(Decimal(str(price)) * Decimal(str(ticker.ratio)))

    # ポートフォリオの成長率を計算
    total_end_of_2022_value = sum(end_of_2022_prices)
    total_latest_value = sum(latest_prices)

    if total_end_of_2022_value == 0:
        growth_rate = 1
    else:
        growth_rate = (
            (total_latest_value - total_end_of_2022_value) / total_end_of_2022_value) - 1

    session.close()

    return growth_rate


async def getPriceData(db: Session, portfolio_id: int):
    # PortfolioPriceDataオブジェクトを初期化
    portfolio_price_data = schemas.PortfolioCompositePriceByDate(
        composite_price_by_date=[])

    # portfolio_idに紐づく2023/1/1以降の全ticker, 日付のPriceデータを取得
    date_threshold = _dt.date(2023, 1, 1)

    query_result = db.query(models.TickerPrice).\
        join(models.Ticker, models.TickerPrice.ticker == models.Ticker.ticker).\
        filter(and_(models.Ticker.portfolio_id == portfolio_id, models.TickerPrice.date >= date_threshold)).\
        with_entities(models.TickerPrice.date,
                      models.TickerPrice.ticker, models.TickerPrice.price, models.Ticker.ratio).all()

    # 1. Convert each result in query_result to a TickerPriceModel object
    ticker_price_models = [schemas.TickerPriceModel(
        ticker=result[1], price=result[2], ratio=result[3]) for result in query_result]

    # 2. Group results by date
    date_grouped_ticker_prices = defaultdict(list)
    for date, ticker_price_model in zip((result[0] for result in query_result), ticker_price_models):
        # Ensure that the date is a datetime object
        if isinstance(date, _dt.date) and not isinstance(date, _dt.datetime):
            date = _dt.datetime.combine(date, _dt.time.min)
        date_grouped_ticker_prices[date].append(ticker_price_model)

    # 3. Create DatePricesModel objects using the grouped data
    date_prices_models = [schemas.DatePricesModel(
        date=date, ticker_prices=ticker_prices) for date, ticker_prices in date_grouped_ticker_prices.items()]

    earliest_composite_price = None
    peak_price = None
    trough_price = None
    latest_price = None

    for i, date_data in enumerate(date_prices_models):
        composite_price = 0
        # calculate composite price
        for ticker_data in date_data.ticker_prices:
            composite_price += ticker_data.ratio * ticker_data.price

        if i == 0:
            earliest_composite_price = composite_price
            ratio = 0.0
        else:
            ratio = (composite_price / earliest_composite_price) - 1

        composite_price_data = {
            "date": date_data.date, "composite_price": ratio}

        portfolio_price_data.composite_price_by_date.append(
            composite_price_data)

        # Update peak and trough prices
        if peak_price is None or composite_price_data['composite_price'] > peak_price['composite_price']:
            peak_price = composite_price_data

        if trough_price is None or composite_price_data['composite_price'] < trough_price['composite_price']:
            trough_price = composite_price_data

        # Update the latest price
        if latest_price is None or composite_price_data['date'] > latest_price['date']:
            latest_price = composite_price_data

    portfolio_price_data.latest_performance = latest_price['composite_price']
    portfolio_price_data.peak = peak_price['composite_price']
    portfolio_price_data.trough = trough_price['composite_price']
    portfolio_price_data.max_drow_down = peak_price['composite_price'] - \
        trough_price['composite_price']

    return portfolio_price_data


async def getTickerMaster(db: Session):
    ticker_master = schemas.TickerMaster(
        tickers=[])

    result = db.query(models.TickerMaster)\
        .join(models.TickerPrice, models.TickerMaster.ticker == models.TickerPrice.ticker)\
        .distinct()\
        .all()

    for ticker in result:
        # print(ticker.ticker)
        ticker_master.tickers.append(ticker.ticker)

    return ticker_master


async def getPortfolioByUserId(db: Session, user_id: int):
    print("Utils function-User ID:", user_id)
    portfolios = db.query(models.Portfolio).filter(
        models.Portfolio.user_id == user_id).all()
    print("Utils function-portfolio data:", portfolios)
    return portfolios
