from fastapi import FastAPI, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

from .models import User, TermSheet, UserCreate, TermSheetCreate

app = FastAPI(title="User Service API")

# Mock data storage
users_db = {}
term_sheets_db = {}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    user_id = str(uuid.uuid4())
    now = datetime.now()
    new_user = User(
        id=user_id,
        email=user.email,
        client_identifier=user.client_identifier,
        created_at=now
    )
    users_db[user_id] = new_user
    return new_user

@app.get("/term-sheets/{term_sheet_id}")
async def get_term_sheet(term_sheet_id: str):
    # Search by the legacy term_sheet_id field
    for ts in term_sheets_db.values():
        if ts.term_sheet_id == term_sheet_id:
            return ts
    raise HTTPException(status_code=404, detail="Term sheet not found")

@app.post("/term-sheets", response_model=TermSheet)
async def create_term_sheet(term_sheet: TermSheetCreate):
    ts_id = str(uuid.uuid4())
    # Generate legacy string ID - THIS IS WHAT WE WANT TO CHANGE
    legacy_id = f"TS_{datetime.now().strftime('%Y%m%d')}_{len(term_sheets_db):03d}"
    
    new_ts = TermSheet(
        id=ts_id,
        term_sheet_id=legacy_id,  # String-based ID
        user_id=term_sheet.user_id,
        amount=term_sheet.amount,
        created_at=datetime.now()
    )
    term_sheets_db[ts_id] = new_ts
    return new_ts

@app.get("/users/{user_id}/term-sheets")
async def get_user_term_sheets(user_id: str):
    user_term_sheets = []
    for ts in term_sheets_db.values():
        if ts.user_id == user_id:
            user_term_sheets.append(ts)
    return user_term_sheets

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}