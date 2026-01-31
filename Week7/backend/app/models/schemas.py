"""
Pydantic 数据模型定义
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Slide(BaseModel):
    """幻灯片模型"""
    id: str
    text: str
    image_path: Optional[str] = None
    content_hash: str
    image_hash: Optional[str] = None


class ProjectState(BaseModel):
    """项目状态模型"""
    style_reference: Optional[str] = None
    slides: list[Slide] = []


class StylePrompt(BaseModel):
    """风格提示模型"""
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="风格描述,用于生成候选图片"
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """验证描述不为空"""
        v = v.strip()
        if not v:
            raise ValueError("风格描述不能为空或仅包含空白字符")
        return v


class StyleCandidate(BaseModel):
    """风格候选模型"""
    image_path: str


class SelectedStyle(BaseModel):
    """选中风格模型"""
    image_path: str = Field(
        ...,
        min_length=1,
        description="选中的风格图片路径"
    )
    
    @field_validator('image_path')
    @classmethod
    def validate_image_path(cls, v: str) -> str:
        """验证图片路径格式"""
        v = v.strip()
        if not v:
            raise ValueError("图片路径不能为空")
        return v


class SlideCreate(BaseModel):
    """创建幻灯片请求"""
    text: str


class SlideUpdate(BaseModel):
    """更新幻灯片请求"""
    text: str
