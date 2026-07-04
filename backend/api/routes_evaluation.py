from fastapi import APIRouter

from backend.schemas.evaluation import EvaluationRequest
from backend.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])

evaluation_service = EvaluationService()


@router.post("")
async def run_evaluation(request: EvaluationRequest):
    return await evaluation_service.run_evaluation(sample_size=request.sample_size)
