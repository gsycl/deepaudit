from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    full_name: str
    risk_score: int
    status: str
    program_type: str
    is_deceased: bool
    ai_recommendation: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    weight: int


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
