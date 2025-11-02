from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter()

@router.get("/users", response_model=List[dict])
async def get_users():

    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com"
        }
    ]