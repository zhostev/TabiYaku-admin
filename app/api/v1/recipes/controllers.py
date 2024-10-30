# app/api/v1/recipes/controllers.py

import base64
import logging
import requests
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from starlette.status import HTTP_400_BAD_REQUEST
from tortoise.contrib.fastapi import HTTPNotFoundError

from .schemas import (
    RecipeRecognitionRequest,
    RecipeRecognitionResponse,
    RecipeRecognitionQueryResponse
)
from .models import RecipeRecognition
from app.core.dependency import get_gpt_client, DependPermisson  # 修正导入

router = APIRouter()

from app.log.log import logger  # 使用绝对导入

def encode_image_bytes(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

@router.post("/recognize", response_model=RecipeRecognitionResponse, dependencies=[DependPermisson])
async def recognize_recipe(
    request: RecipeRecognitionRequest, 
    gpt_client=Depends(get_gpt_client)
):
    logger.info(f"开始识别图像: {request.image_url}")
    
    # 下载图像
    try:
        response = requests.get(request.image_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"下载图像失败: {e}")
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="无法下载图像")
    
    image_bytes = response.content
    base64_image = encode_image_bytes(image_bytes)
    
    # 调用大模型识别
    try:
        gpt_response = gpt_client.ChatCompletion.create(
            model="gpt-4",  # 根据实际情况调整模型名称
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds in Markdown."},
                {"role": "user", "content": [
                    {"type": "text", "text": "请将以下日语菜单图片识别为中文文本菜谱："},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]}
            ],
            temperature=0.0,
        )
        recognized_text = gpt_response.choices[0].message.content
        logger.info("大模型识别成功")
    except Exception as e:
        logger.error(f"大模型调用失败: {e}")
        raise HTTPException(status_code=500, detail="大模型调用失败")
    
    # 保存识别记录
    record = await RecipeRecognition.create(
        image_url=request.image_url,
        base64_image=base64_image,
        recognized_text=recognized_text
    )
    logger.info(f"已保存识别记录 ID: {record.id}")
    
    return RecipeRecognitionResponse(
        id=record.id,
        recognized_text=record.recognized_text,
        created_at=record.created_at.isoformat()
    )

@router.get("/recognitions", response_model=List[RecipeRecognitionQueryResponse], dependencies=[DependPermisson])
async def get_recognitions(skip: int = 0, limit: int = Query(10, le=100)):
    records = await RecipeRecognition.all().order_by("-created_at").offset(skip).limit(limit)
    return [
        RecipeRecognitionQueryResponse(
            id=record.id,
            image_url=record.image_url,
            recognized_text=record.recognized_text,
            created_at=record.created_at.isoformat()
        )
        for record in records
    ]

@router.get("/recognitions/{recognition_id}", response_model=RecipeRecognitionQueryResponse, responses={404: {"model": HTTPNotFoundError}}, dependencies=[DependPermisson])
async def get_recognition(recognition_id: int):
    record = await RecipeRecognition.get_or_none(id=recognition_id)
    if not record:
        raise HTTPException(status_code=404, detail="识别记录未找到")
    return RecipeRecognitionQueryResponse(
        id=record.id,
        image_url=record.image_url,
        recognized_text=record.recognized_text,
        created_at=record.created_at.isoformat()
    )