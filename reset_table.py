import database as _database
import models as _models
import services as _services


def drop_tables():
    _database.Base.metadata.drop_all(bind=_database.engine)


def create_tables():
    _services._add_tables()


if __name__ == "__main__":
    print("Dropping tables...")
    drop_tables()
    print("Tables dropped.")
    print("Creating tables...")
    create_tables()
    print("Tables created.")
