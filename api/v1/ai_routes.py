from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai.ai_service import AIService

router = APIRouter()


class AIProblemRequest(BaseModel):
    difficulty: str
    topic: str
    tags: list | None = None
    concept: str | None = None
    language: str | None = None
    additional_requirements: str | None = None


@router.post("/api/ai/problems/generate")
async def generate_problem(request: AIProblemRequest):
    try:
        ai = AIService()
        result = await ai.generate_problem(request.dict())
        return {"status": "ok", "generated": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
