# api/v1/recipes/__init__.py
from fastapi import APIRouter

from .controllers import router

recipes_router = APIRouter()
recipes_router.include_router(router, tags=["菜谱识别模块"])

__all__ = ["recipes_router"]