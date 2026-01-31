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
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
yaml_store = YAMLStore()
generator = GeminiGenerator(api_key=config.GEMINI_API_KEY)


@router.get("/project", response_model=ProjectState)
async def get_project():
    """获取完整项目状态"""
    data = yaml_store.get_project_state()
    return ProjectState(**data)


@router.post("/test/reset")
async def reset_project_for_testing():
    """
    重置项目状态 (仅用于测试)
    
    WARNING: This endpoint is for testing purposes only!
    """
    logger.warning("Resetting project state for testing")
    
    try:
        # 使用 YAMLStore 的重置方法
        yaml_store.reset()
        
        logger.info("Project state reset successfully")
        return {"message": "Project reset successfully", "status": "ok"}
    except Exception as e:
        logger.error(f"Failed to reset project: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.post("/style/init", response_model=list[StyleCandidate])
async def init_style(prompt: StylePrompt):
    """
    生成风格候选图
    
    Args:
        prompt: 包含风格描述的请求体
    
    Returns:
        list[StyleCandidate]: 2张候选图片的路径列表
    
    Raises:
        HTTPException 400: 输入验证失败
        HTTPException 500: 图片生成失败
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
        logger.info(f"Generating style candidates for: {description[:50]}...")
        image_paths = generator.generate_style_candidates(description)
        
        # 验证生成的图片路径
        if not image_paths or len(image_paths) != 2:
            logger.error(f"Generator returned invalid paths: {image_paths}")
            raise HTTPException(
                status_code=500,
                detail="图片生成失败: 返回的图片数量不正确"
            )
        
        # 在 stub 模式下,图片文件不会真正存在
        # 在实际使用 Gemini API 时,应该验证文件是否存在
        logger.info(f"Successfully generated {len(image_paths)} style candidates")
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
async def select_style(selected: SelectedStyle):
    """
    保存选定的风格
    
    Args:
        selected: 包含选中图片路径的请求体
    
    Returns:
        ProjectState: 更新后的完整项目状态
    
    Raises:
        HTTPException 400: 图片路径无效或不存在
        HTTPException 500: YAML 写入失败
    """
    # 验证输入
    image_path = selected.image_path.strip()
    if not image_path:
        logger.warning("Style select called with empty image_path")
        raise HTTPException(
            status_code=400,
            detail="图片路径不能为空"
        )
    
    # 验证图片路径格式 (应该指向 assets/ 目录)
    if "assets" not in image_path:
        logger.warning(f"Invalid image path format: {image_path}")
        raise HTTPException(
            status_code=400,
            detail="图片路径格式无效"
        )
    
    # 在实际生产环境中,应该验证文件是否真实存在
    # 在 stub 模式下,我们跳过文件存在性检查
    # 如果启用了真实的 Gemini API,取消以下注释:
    # path_obj = Path(image_path)
    # if not path_obj.exists() or not path_obj.is_file():
    #     logger.error(f"Selected image file not found: {image_path}")
    #     raise HTTPException(
    #         status_code=400,
    #         detail="所选图片文件不存在"
    #     )
    
    # 保存风格参考
    try:
        logger.info(f"Saving style reference: {image_path}")
        yaml_store.set_style_reference(image_path)
        
        # 获取更新后的项目状态
        data = yaml_store.get_project_state()
        
        # 验证更新是否成功
        if data.get("style_reference") != image_path:
            logger.error("Style reference was not saved correctly")
            raise HTTPException(
                status_code=500,
                detail="风格保存失败: 验证失败"
            )
        
        logger.info(f"Successfully saved style reference")
        return ProjectState(**data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error saving style reference: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"风格保存失败: {str(e)}"
        )


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
