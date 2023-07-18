import datetime as _dt
import sqlalchemy as _sql
import database as _database
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from database import Base
from database import engine
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


class Portfolio(_database.Base):
    __tablename__ = "portfolios"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    # growth = _sql.Column(_sql.REAL)
    date_created = _sql.Column(
        _sql.DateTime, default=_dt.datetime.now())
    date_updated = _sql.Column(_sql.DateTime, default=_dt.datetime.now(
    ), onupdate=_dt.datetime.now())
    user_id = _sql.Column(_sql.Integer, ForeignKey(
        "users.id"), index=True)  # 追加
    is_primary = _sql.Column(_sql.Boolean, default=False)  # 新しいカラム


class Ticker(_database.Base):
    __tablename__ = "tickers"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    portfolio_id = _sql.Column(
        _sql.Integer, ForeignKey("portfolios.id"), index=True)
    ticker = _sql.Column(_sql.String, nullable=False, index=True)
    ratio = _sql.Column(Integer, nullable=False)
    date_created = _sql.Column(
        _sql.DateTime, default=_dt.datetime.now())
    date_updated = _sql.Column(_sql.DateTime, default=_dt.datetime.now(
    ), onupdate=_dt.datetime.now())

    Portfolio = relationship("Portfolio", backref="tickers")


class TickerMaster(Base):
    __tablename__ = "ticker_master"

    id = _sql.Column(Integer, primary_key=True, index=True)
    ticker = _sql.Column(String, nullable=False, index=True)
    exchange = _sql.Column(String, index=True)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    date_updated = _sql.Column(
        _sql.DateTime, default=_dt.datetime.now(), onupdate=_dt.datetime.now())

    # リレーション
    prices = relationship("TickerPrice", back_populates="ticker_master")


class TickerPrice(Base):
    __tablename__ = "ticker_prices"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    ticker = _sql.Column(_sql.String, nullable=False, index=True)
    date = _sql.Column(_sql.Date, nullable=False, index=True)
    price = _sql.Column(_sql.Numeric(precision=8, scale=2), nullable=False)

    date_created = _sql.Column(
        _sql.DateTime, default=_dt.datetime.now())
    date_updated = _sql.Column(_sql.DateTime, default=_dt.datetime.now(
    ), onupdate=_dt.datetime.now())

    # リレーション
    ticker_master_id = _sql.Column(_sql.Integer, _sql.ForeignKey(
        "ticker_master.id", ondelete="CASCADE"), index=True)
    ticker_master = relationship("TickerMaster", back_populates="prices")


class User(_database.Base):
    __tablename__ = "users"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    username = _sql.Column(_sql.String, index=True)
    email = _sql.Column(_sql.String, unique=True, index=True)
    hashed_password = _sql.Column(String)
    avatar_url = _sql.Column(_sql.String)
    google_id = _sql.Column(_sql.String, unique=True,
                            index=True)  # Googleから提供される固有のID
    is_active = _sql.Column(_sql.Boolean(), default=True)
    is_superuser = _sql.Column(_sql.Boolean(), default=False)
