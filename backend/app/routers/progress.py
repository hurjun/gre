"""HTTP routes reporting per-subgroup level and solved/total counts."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import level_bounds
from ..database import get_db
from ..models import Subgroup
from ..schemas import ProgressOut, SubgroupProgressOut
from ..services import adaptive

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("", response_model=ProgressOut)
def get_progress(db: Session = Depends(get_db)) -> ProgressOut:
    """Current level and solved/total counts for every subgroup."""
    subgroups = []
    for subgroup in Subgroup:
        progress = adaptive.get_or_create_progress(db, subgroup.value)
        solved, total = adaptive.subgroup_stats(db, subgroup.value)
        _, max_level = level_bounds(subgroup.value)
        subgroups.append(
            SubgroupProgressOut(
                subgroup=subgroup,
                current_level=progress.current_level,
                max_level=max_level,
                solved=solved,
                total=total,
            )
        )
    db.commit()
    return ProgressOut(subgroups=subgroups)
