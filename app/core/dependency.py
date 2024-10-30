# app/core/dependency.py

from typing import Optional
import jwt
from fastapi import Depends, Header, HTTPException, Request
from functools import lru_cache
import openai
import os
from dotenv import load_dotenv

from app.core.ctx import CTX_USER_ID
from app.models import Role, User
from app.settings import settings

# 加载环境变量
load_dotenv()

class AuthControl:
    @classmethod
    async def is_authed(cls, token: str = Header(..., description="token验证")) -> Optional["User"]:
        try:
            if token == "dev":
                user = await User.filter().first()
                if not user:
                    raise HTTPException(status_code=401, detail="未找到用户")
                user_id = user.id
            else:
                decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
                user_id = decode_data.get("user_id")
                if not user_id:
                    raise HTTPException(status_code=401, detail="Token中未包含用户ID")
            user = await User.filter(id=user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="Authentication failed")
            CTX_USER_ID.set(int(user_id))
            return user
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="无效的Token")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="登录已过期")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{repr(e)}")

class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path
        roles: list[Role] = await current_user.roles
        if not roles:
            raise HTTPException(status_code=403, detail="The user is not bound to a role")
        # 获取所有角色的 API 权限
        apis = []
        for role in roles:
            role_apis = await role.apis
            apis.extend(role_apis)
        permission_apis = set((api.method, api.path) for api in apis)
        if (method, path) not in permission_apis:
            raise HTTPException(status_code=403, detail=f"Permission denied method:{method} path:{path}")

DependAuth = Depends(AuthControl.is_authed)
DependPermisson = Depends(PermissionControl.has_permission)

@lru_cache()
def get_gpt_client():
    api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment variables or settings.")
    openai.api_key = api_key
    return openai