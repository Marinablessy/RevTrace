from pydantic import BaseModel
from typing import Optional


class ProspectCreate(BaseModel):
    name: str
    company: str
    industry: str
    role: str
    company_size: str
    pain_point: str


class Prospect(ProspectCreate):
    prospect_id: str
    account_id: str

    message_angle: Optional[str] = None
    message_sent: Optional[str] = None
    outcome: Optional[str] = None


class OutcomeUpdate(BaseModel):
    outcome: str


class GenerateMessageRequest(BaseModel):
    recommended_angle: str
    memories: list[str]