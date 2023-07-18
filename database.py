import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _declarative
import sqlalchemy.orm as _orm

SQLALCHEMY_DATABASE_URL = "postgresql://wizard_app:password@localhost:5432/wizards_database"

engine = _sql.create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = _orm.sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

Base = _declarative.declarative_base()
