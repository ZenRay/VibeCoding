"""
API 端点定义（支持多版本项目管理）
"""
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import (
    ProjectState, StylePrompt, StyleCandidate, SelectedStyle,
    SlideCreate, SlideUpdate, Slide
)
from app.data.yaml_store import YAMLStore
from app.core.generator import GeminiGenerator
from app.core.config import config
import uuid
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# 全局 YAMLStore 用于版本管理（不绑定特定版本）
version_manager = YAMLStore(version=None)

# 缓存已初始化的 generator（按版本）
_generators: dict[int, tuple[YAMLStore, GeminiGenerator]] = {}


def get_version_resources(version: int) -> tuple[YAMLStore, GeminiGenerator]:
    """
    获取或创建指定版本的 YAMLStore 和 GeminiGenerator
    
    Args:
        version: 版本号
        
    Returns:
        tuple: (yaml_store, generator)
    """
    if version not in _generators:
        # 创建新的 yaml_store 和 generator
        yaml_store = YAMLStore(version=version)
        generator = GeminiGenerator(
            api_key=config.GEMINI_API_KEY,
            model=config.GEMINI_MODEL,
            mode=config.AI_MODE,
            yaml_store=yaml_store,
            provider=config.AI_PROVIDER,
            openrouter_api_key=config.OPENROUTER_API_KEY,
            openrouter_model=config.OPENROUTER_MODEL,
            image_size=config.IMAGE_SIZE,
            image_aspect_ratio=config.IMAGE_ASPECT_RATIO,
            version=version  # 绑定版本
        )
        _generators[version] = (yaml_store, generator)
        logger.info(f"Initialized resources for version {version}")
    
    return _generators[version]


# ============ 版本管理端点 ============

@router.get("/versions")
async def list_versions():
    """
    列出所有可用版本
    
    Returns:
        list: 版本信息列表，包含 version, created_at, slide_count 等
    """
    try:
        versions = version_manager.list_versions()
        
        # 获取每个版本的详细信息
        version_list = []
        for v in versions:
            info = version_manager.get_version_info(v)
            if info:
                version_list.append(info)
        
        logger.info(f"Listed {len(version_list)} versions")
        return {"versions": version_list}
        
    except Exception as e:
        logger.exception(f"Error listing versions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list versions: {str(e)}"
        )


@router.get("/versions/{version}")
async def get_version_info(version: int):
    """
    获取指定版本的摘要信息
    
    Args:
        version: 版本号
        
    Returns:
        dict: 版本信息
    """
    info = version_manager.get_version_info(version)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Version {version} not found"
        )
    
    return info


@router.post("/versions/create")
async def create_new_version(prompt: Optional[StylePrompt] = None):
    """
    创建新版本（不初始化风格，返回版本号）
    
    Args:
        prompt: 风格描述（可选，仅保存不生成）
        
    Returns:
        dict: {"version": 新版本号}
    """
    try:
        style_prompt = prompt.description if prompt else None
        new_version = version_manager.create_new_version(style_prompt=style_prompt)
        
        logger.info(f"Created new version {new_version}")
        return {
            "version": new_version,
            "message": "New version created successfully"
        }
        
    except Exception as e:
        logger.exception(f"Error creating new version: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create new version: {str(e)}"
        )


# ============ 项目数据端点（需要版本参数）============

@router.get("/project", response_model=ProjectState)
async def get_project(version: int = Query(..., description="版本号")):
    """
    获取指定版本的完整项目状态
    
    Args:
        version: 版本号（必需）
        
    Returns:
        ProjectState: 项目状态
    """
    try:
        yaml_store, _ = get_version_resources(version)
        data = yaml_store.get_project_state()
        return ProjectState(**data)
        
    except Exception as e:
        logger.exception(f"Error getting project for version {version}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project: {str(e)}"
        )


@router.post("/test/reset")
async def reset_project_for_testing(version: int = Query(...)):
    """
    重置指定版本的项目状态 (仅用于测试)
    
    WARNING: This endpoint is for testing purposes only!
    """
    logger.warning(f"Resetting project state for version {version}")
    
    try:
        yaml_store, _ = get_version_resources(version)
        yaml_store.reset()
        
        logger.info(f"Version {version} reset successfully")
        return {"message": f"Version {version} reset successfully", "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to reset version {version}: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# ============ 风格管理端点 ============

@router.post("/style/init", response_model=list[StyleCandidate])
async def init_style(
    prompt: StylePrompt,
    version: int = Query(..., description="版本号")
):
    """
    为指定版本生成风格候选图
    
    Args:
        prompt: 包含风格描述的请求体
        version: 版本号
    
    Returns:
        list[StyleCandidate]: 2张候选图片的路径列表
    """
    # 输入验证
    description = prompt.description.strip()
    if not description:
        logger.warning("Style init called with empty description")
        raise HTTPException(
            status_code=400,
            detail="风格描述不能为空"
        )
    
    if len(description) > 500:
        logger.warning(f"Style description too long: {len(description)} chars")
        raise HTTPException(
            status_code=400,
            detail="风格描述不能超过500个字符"
        )
    
    # 生成风格候选图
    try:
        _, generator = get_version_resources(version)
        
        logger.info(f"Generating style candidates for version {version}: {description[:50]}...")
        image_paths = generator.generate_style_candidates(description)
        
        # 验证生成的图片路径
        if not image_paths or len(image_paths) != 2:
            logger.error(f"Generator returned invalid paths: {image_paths}")
            raise HTTPException(
                status_code=500,
                detail="图片生成失败: 返回的图片数量不正确"
            )
        
        logger.info(f"Successfully generated {len(image_paths)} style candidates for version {version}")
        return [StyleCandidate(image_path=path) for path in image_paths]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in style init: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"图片生成失败: {str(e)}"
        )


@router.post("/style/select", response_model=ProjectState)
async def select_style(
    selected: SelectedStyle,
    version: int = Query(..., description="版本号")
):
    """
    保存指定版本的选定风格
    
    Args:
        selected: 包含选中图片路径的请求体
        version: 版本号
    
    Returns:
        ProjectState: 更新后的完整项目状态
    """
    # 验证输入
    image_path = selected.image_path.strip()
    if not image_path:
        logger.warning("Style select called with empty image_path")
        raise HTTPException(
            status_code=400,
            detail="图片路径不能为空"
        )
    
    # 验证图片路径格式 (应该指向 assets/vX/ 目录)
    if f"assets/v{version}/" not in image_path:
        logger.warning(f"Invalid image path for version {version}: {image_path}")
        raise HTTPException(
            status_code=400,
            detail=f"图片路径必须属于版本 {version}"
        )
    
    # 保存风格参考和 prompt
    try:
        yaml_store, _ = get_version_resources(version)
        
        logger.info(f"Saving style reference for version {version}: {image_path}, prompt: {selected.style_prompt}")
        yaml_store.set_style_reference(image_path, selected.style_prompt)
        
        # 获取更新后的项目状态
        data = yaml_store.get_project_state()
        
        # 验证更新是否成功
        if data.get("style_reference") != image_path:
            logger.error("Style reference was not saved correctly")
            raise HTTPException(
                status_code=500,
                detail="风格保存失败: 验证失败"
            )
        
        logger.info(f"Successfully saved style reference and prompt for version {version}")
        return ProjectState(**data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error saving style reference: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"风格保存失败: {str(e)}"
        )


# ============ 幻灯片管理端点 ============

@router.post("/slides", response_model=Slide)
async def create_slide(
    slide_data: SlideCreate,
    version: int = Query(..., description="版本号")
):
    """为指定版本创建新幻灯片"""
    yaml_store, _ = get_version_resources(version)
    
    slide_id = str(uuid.uuid4())
    slide = yaml_store.add_slide(slide_id, slide_data.text)
    return Slide(**slide)


@router.put("/slides/reorder", response_model=ProjectState)
async def reorder_slides(
    slide_ids: list[str],
    version: int = Query(..., description="版本号")
):
    """更新指定版本的幻灯片顺序"""
    yaml_store, _ = get_version_resources(version)
    
    yaml_store.reorder_slides(slide_ids)
    data = yaml_store.get_project_state()
    return ProjectState(**data)


@router.put("/slides/{slide_id}", response_model=Slide)
async def update_slide(
    slide_id: str,
    slide_data: SlideUpdate,
    version: int = Query(..., description="版本号")
):
    """更新指定版本的幻灯片文本和/或图片路径"""
    yaml_store, _ = get_version_resources(version)
    
    slide = yaml_store.update_slide(
        slide_id, 
        text=slide_data.text,
        image_path=slide_data.image_path
    )
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    return Slide(**slide)


@router.post("/slides/{slide_id}/generate", response_model=Slide)
async def regenerate_image(
    slide_id: str,
    version: int = Query(..., description="版本号")
):
    """重新生成指定版本的幻灯片图片"""
    yaml_store, generator = get_version_resources(version)
    
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
async def delete_slide(
    slide_id: str,
    version: int = Query(..., description="版本号")
):
    """删除指定版本的幻灯片"""
    yaml_store, _ = get_version_resources(version)
    
    success = yaml_store.delete_slide(slide_id)
    if not success:
        raise HTTPException(status_code=404, detail="Slide not found")
    return {"message": "Slide deleted successfully"}
