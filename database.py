from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import Base
from flask_sqlalchemy import SQLAlchemy

engine = create_engine('sqlite:///paper_trading.db')
db_session = scoped_session(sessionmaker(bind=engine))

def init_db():
    # Import all modules here that might define models
    import models
    Base.metadata.create_all(engine) 