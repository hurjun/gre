"""Application configuration, overridable through environment variables."""

import os

DATABASE_URL = os.getenv(
    "GRE_DATABASE_URL",
    "mysql+pymysql://gre:gre@localhost:3306/gre",
)

CORS_ORIGINS = os.getenv("GRE_CORS_ORIGINS", "http://localhost:5173").split(",")

MIN_LEVEL = 1
MAX_LEVEL = 5
