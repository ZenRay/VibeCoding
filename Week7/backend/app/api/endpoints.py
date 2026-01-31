"""
API 端点定义
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ProjectState, StylePrompt, StyleCandidate, SelectedStyle,
    SlideCreate, SlideUpdate, Slide
)
from app.data.yaml_store import YAMLStore
from app.core.generator import GeminiGenerator
from app.core.config import config
import uuid

router = APIRouter(prefix="/api")
yaml_store = YAMLStore()
generator = GeminiGenerator(api_key=config.GEMINI_API_KEY)


@router.get("/project", response_model=ProjectState)
async def get_project():
    """获取完整项目状态"""
    data = yaml_store.get_project_state()
    return ProjectState(**data)


@router.post("/style/init", response_model=list[StyleCandidate])
async def init_style(prompt: StylePrompt):
    """生成风格候选图"""
    image_paths = generator.generate_style_candidates(prompt.description)
    return [StyleCandidate(image_path=path) for path in image_paths]


@router.post("/style/select", response_model=ProjectState)
async def select_style(selected: SelectedStyle):
    """保存选定的风格"""
    yaml_store.set_style_reference(selected.image_path)
    data = yaml_store.get_project_state()
    return ProjectState(**data)


@router.post("/slides", response_model=Slide)
async def create_slide(slide_data: SlideCreate):
    """创建新幻灯片"""
    slide_id = str(uuid.uuid4())
    slide = yaml_store.add_slide(slide_id, slide_data.text)
    return Slide(**slide)


@router.put("/slides/reorder", response_model=ProjectState)
async def reorder_slides(slide_ids: list[str]):
    """更新幻灯片顺序"""
    yaml_store.reorder_slides(slide_ids)
    data = yaml_store.get_project_state()
    return ProjectState(**data)


@router.put("/slides/{slide_id}", response_model=Slide)
async def update_slide(slide_id: str, slide_data: SlideUpdate):
    """更新幻灯片文本"""
    slide = yaml_store.update_slide(slide_id, text=slide_data.text)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    return Slide(**slide)


@router.post("/slides/{slide_id}/generate", response_model=Slide)
async def regenerate_image(slide_id: str):
    """重新生成幻灯片图片"""
    data = yaml_store.get_project_state()
    
    # 找到对应的幻灯片
    slide_dict = next((s for s in data["slides"] if s["id"] == slide_id), None)
    if not slide_dict:
        raise HTTPException(status_code=404, detail="Slide not found")
    
    # 生成图片
    style_ref = data.get("style_reference")
    if not style_ref:
        raise HTTPException(status_code=400, detail="Style reference not set")
    
    image_path = generator.generate_slide_image(slide_dict["text"], style_ref)
    
    # 更新幻灯片
    slide = yaml_store.update_slide(slide_id, image_path=image_path)
    return Slide(**slide)


@router.delete("/slides/{slide_id}")
async def delete_slide(slide_id: str):
    """删除幻灯片"""
    success = yaml_store.delete_slide(slide_id)
    if not success:
        raise HTTPException(status_code=404, detail="Slide not found")
    return {"message": "Slide deleted successfully"}
