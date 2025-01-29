from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    balance = Column(Float, default=100000.00)  # Starting balance of $100,000
    created_at = Column(DateTime, default=datetime.utcnow)

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String(10))
    quantity = Column(Float)
    price = Column(Float)
    trade_type = Column(String(4))  # 'buy' or 'sell'
    timestamp = Column(DateTime, default=datetime.utcnow)

class Portfolio(Base):
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String(10))
    quantity = Column(Float)
    average_price = Column(Float)

class LimitOrder(Base):
    __tablename__ = 'limit_orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    symbol = Column(String(10))
    quantity = Column(Float)
    target_price = Column(Float)
    order_type = Column(String(4))  # 'buy' or 'sell'
    status = Column(String(10))  # 'pending', 'executed', 'cancelled'
    created_at = Column(DateTime, default=datetime.utcnow) 