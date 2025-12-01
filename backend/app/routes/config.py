from fastapi import APIRouter
from app.core.configs import get_default_config
from app.models.config import RunConfig

router = APIRouter()


@router.get("/default", response_model=RunConfig)
async def get_default_config_endpoint():
    """Get default configuration constants"""
    return get_default_config()
