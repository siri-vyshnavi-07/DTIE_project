import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartride_dev.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Demo route. Replace with the actual route and fare table for your transport service.
STOPS = [
    {"id": 1, "name": "MVP Colony", "sequence": 1},
    {"id": 2, "name": "Madhurawada", "sequence": 2},
    {"id": 3, "name": "Hanumanthawaka", "sequence": 3},
    {"id": 4, "name": "RTC Complex", "sequence": 4},
    {"id": 5, "name": "Dwaraka Nagar", "sequence": 5},
]
FARE_PER_STOP = 10
MINIMUM_FARE = 10
