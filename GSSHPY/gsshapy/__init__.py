
from sqlalchemy.orm import scoped_session, sessionmaker

# Global session manager: DBSession() returns the Thread-local
# session object appropriate for the current web request.
maker = sessionmaker(autoflush=True, autocommit=False)

DBSession = scoped_session(maker)

def init_model(engine):
    """Call this before using any of the tables or classes in the model."""
    DBSession.configure(bind=engine)

