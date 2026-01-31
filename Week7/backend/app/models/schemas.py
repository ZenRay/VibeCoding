"""
Pydantic 数据模型定义
"""
from typing import Optional
from pydantic import BaseModel


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
    description: str


class StyleCandidate(BaseModel):
    """风格候选模型"""
    image_path: str


class SelectedStyle(BaseModel):
    """选中风格模型"""
    image_path: str


class SlideCreate(BaseModel):
    """创建幻灯片请求"""
    text: str


class SlideUpdate(BaseModel):
    """更新幻灯片请求"""
    text: str
