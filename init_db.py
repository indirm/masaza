"""Run this once to initialize the database."""
from app import app, db, seed_database

with app.app_context():
    db.create_all()
    seed_database()
    print("Database initialized!")
