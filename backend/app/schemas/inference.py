from pydantic import BaseModel
from typing import List, Literal, Optional

class DomainResult(BaseModel):
    domain: Literal['hr', 'finance', 'healthcare', 'ecommerce', 'iot_sensor', 'generic']
    confidence: float
    evidence: List[str]

class Inference(BaseModel):
    id: str
    severity: Literal['critical', 'warning', 'info', 'suggestion']
    category: Literal['data_quality', 'ml_readiness', 'structure', 'statistics', 'consistency']
    title: str
    detail: str
    affected_columns: List[str]
    suggested_action: str
    auto_fixable: bool
    fix_operation: Optional[str] = None

class InferenceReport(BaseModel):
    domain_detection: DomainResult
    general_inferences: List[Inference]
    domain_inferences: List[Inference]
    all_inferences: List[Inference]
    critical_count: int
    warning_count: int
    info_count: int
    suggestion_count: int
    ml_readiness_score: float
    ml_readiness_label: Literal['Not Ready', 'Needs Work', 'Almost Ready', 'Ready']
    top_actions: List[str]
