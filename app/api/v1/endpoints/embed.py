from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.models.embed import EmbedRequest, EmbedResponse
from app.services.embed.embed_service import get_embed_service

router = APIRouter()

@router.post("/embed", response_model=EmbedResponse)
async def embed_text(
    request: EmbedRequest,
    service = Depends(get_embed_service)
):
    result = await service.process_embed(
        request.user_id, 
        request.azure_url
    )
    return EmbedResponse(**result)