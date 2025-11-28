# reset_db.py
from app.db.database import Base, engine
from app.models.user import User

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete!")

if __name__ == "__main__":
    reset_database()
