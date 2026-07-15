from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///data/gamescout.db"
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """ "
    Crea la base de datos y sus tablas correspondientes.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """
    Retorna una sesion de la base de datos
    """
    return Session(engine)
