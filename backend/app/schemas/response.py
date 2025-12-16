"""
通用响应模型
"""
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field


T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """
    统一响应模型
    
    Args:
        code: 响应码，200表示成功
        message: 响应消息
        data: 响应数据
    """
    code: int = Field(default=200, description="响应码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {}
            }
        }


class SuccessResponse(BaseModel):
    """
    成功响应模型（带可选数据）
    """
    message: str = Field(description="成功消息")
    data: Optional[Any] = Field(default=None, description="响应数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "操作成功",
                "data": {}
            }
        }


class ErrorResponse(BaseModel):
    """
    错误响应模型
    """
    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    detail: Optional[Any] = Field(default=None, description="错误详情")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 400,
                "message": "Bad Request",
                "detail": "Invalid parameter"
            }
        }
