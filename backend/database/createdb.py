from backend.database.session import engine
from backend.database.models import Base

def create_db():
    # Create all tables in the database (if they don't exist)
    Base.metadata.create_all(bind=engine)

    print("Database and tables created successfully!")
