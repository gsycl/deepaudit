from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.graph_service import build_graph
from ..schemas.graph import GraphData

router = APIRouter()


@router.get("", response_model=GraphData)
def get_fraud_graph(
    min_risk: int = Query(40, ge=0, le=100),
    program_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    data = build_graph(db, min_risk=min_risk, program_type=program_type)
    return GraphData(nodes=data["nodes"], edges=data["edges"])
