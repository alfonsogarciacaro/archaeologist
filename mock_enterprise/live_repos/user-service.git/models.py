from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# User model for the user service
class User(BaseModel):
    id: str
    email: str
    client_identifier: Optional[str] = None
    created_at: datetime
    
class UserCreate(BaseModel):
    email: str
    client_identifier: Optional[str] = None

# Term sheet model
class TermSheet(BaseModel):
    id: str
    term_sheet_id: str  # Legacy string ID that we want to change to UUID
    user_id: str
    amount: float
    status: str = "draft"
    created_at: datetime
    
class TermSheetCreate(BaseModel):
    user_id: str
    amount: float
    # Note: term_sheet_id is currently generated as string