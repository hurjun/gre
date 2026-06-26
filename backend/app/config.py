"""Application configuration, overridable through environment variables."""

import os

from dotenv import load_dotenv

# Load a local ``.env`` (if one exists) so the GRE_* settings below can be set
# without exporting them; see ``.env.example``. A no-op when no file is present.
load_dotenv()

DATABASE_URL = os.getenv(
    "GRE_DATABASE_URL",
    "mysql+pymysql://gre:gre@localhost:3306/gre",
)

CORS_ORIGINS = os.getenv("GRE_CORS_ORIGINS", "http://localhost:5173").split(",")

# Default difficulty range; most sections climb 1-5.
MIN_LEVEL = 1
MAX_LEVEL = 5

# Per-subgroup level bounds. The vocabulary "Word Test" uses a wider 1-10 ladder
# (common words at level 1, rare/hard words at level 10); everything else uses
# the default. Keys are subgroup values from models.Subgroup.
LEVEL_BOUNDS: dict[str, tuple[int, int]] = {
    "vocabulary": (1, 10),
}


def level_bounds(subgroup: str) -> tuple[int, int]:
    """Return the (min_level, max_level) range for a subgroup."""
    return LEVEL_BOUNDS.get(subgroup, (MIN_LEVEL, MAX_LEVEL))
