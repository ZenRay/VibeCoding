"""
YAML 存储层 - 处理 outline.yml 的读写操作
"""
import yaml
import os
from pathlib import Path
from typing import Optional
import hashlib
import logging

logger = logging.getLogger(__name__)


class YAMLStore:
    """YAML 文件存储管理器"""
    
    def __init__(self, file_path: str = "../outline.yml"):
        """
        初始化 YAML 存储
        
        Args:
            file_path: YAML 文件路径，相对于 backend 目录
        """
        base_dir = Path(__file__).parent.parent.parent.parent  # Week7/
        self.file_path = base_dir / file_path.lstrip("../")
        logger.info(f"YAMLStore initialized with path: {self.file_path}")
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保 YAML 文件存在"""
        if not self.file_path.exists():
            logger.warning(f"YAML file does not exist, creating: {self.file_path}")
            self._write_data({"style_reference": None, "slides": []})
            logger.info("Created initial outline.yml")
        else:
            logger.info(f"YAML file exists: {self.file_path}")
    
    def _read_data(self) -> dict:
        """
        读取 YAML 文件内容
        
        Returns:
            dict: YAML 文件内容
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data else {"style_reference": None, "slides": []}
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error: {e}")
            return {"style_reference": None, "slides": []}
        except Exception as e:
            logger.exception(f"Error reading YAML: {e}")
            return {"style_reference": None, "slides": []}
    
    def _write_data(self, data: dict):
        """
        原子写入 YAML 文件
        
        Args:
            data: 要写入的数据
            
        Raises:
            Exception: 写入失败时抛出异常
        """
        try:
            # 原子写入: 先写临时文件,再替换
            temp_path = self.file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
            
            # 替换原文件
            temp_path.replace(self.file_path)
            logger.debug(f"Successfully wrote YAML file")
        except yaml.YAMLError as e:
            logger.error(f"YAML serialization error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Error writing YAML: {e}")
            raise
    
    def get_project_state(self) -> dict:
        """
        获取完整项目状态
        
        Returns:
            dict: 项目状态 (style_reference, slides)
        """
        return self._read_data()
    
    def set_style_reference(self, image_path: str):
        """
        设置风格参考图片
        
        Args:
            image_path: 图片路径
            
        Raises:
            Exception: 写入失败时抛出异常
        """
        if not image_path or not image_path.strip():
            raise ValueError("Image path cannot be empty")
        
        logger.info(f"Setting style reference to: {image_path}")
        data = self._read_data()
        data["style_reference"] = image_path.strip()
        self._write_data(data)
        logger.info("Style reference saved successfully")
    
    def add_slide(self, slide_id: str, text: str, image_path: Optional[str] = None) -> dict:
        """
        添加新幻灯片
        
        Args:
            slide_id: 幻灯片 ID
            text: 文本内容
            image_path: 图片路径 (可选)
        
        Returns:
            dict: 新创建的幻灯片
        """
        data = self._read_data()
        content_hash = hashlib.md5(text.encode()).hexdigest()
        
        new_slide = {
            "id": slide_id,
            "text": text,
            "image_path": image_path,
            "content_hash": content_hash,
            "image_hash": content_hash if image_path else None
        }
        
        data["slides"].append(new_slide)
        self._write_data(data)
        return new_slide
    
    def update_slide(self, slide_id: str, text: Optional[str] = None, 
                    image_path: Optional[str] = None) -> Optional[dict]:
        """
        更新幻灯片
        
        Args:
            slide_id: 幻灯片 ID
            text: 新文本 (可选)
            image_path: 新图片路径 (可选)
        
        Returns:
            dict: 更新后的幻灯片,如果未找到则返回 None
        """
        data = self._read_data()
        
        for slide in data["slides"]:
            if slide["id"] == slide_id:
                if text is not None:
                    slide["text"] = text
                    slide["content_hash"] = hashlib.md5(text.encode()).hexdigest()
                
                if image_path is not None:
                    slide["image_path"] = image_path
                    slide["image_hash"] = slide["content_hash"]
                
                self._write_data(data)
                return slide
        
        return None
    
    def delete_slide(self, slide_id: str) -> bool:
        """
        删除幻灯片
        
        Args:
            slide_id: 幻灯片 ID
        
        Returns:
            bool: 是否删除成功
        """
        data = self._read_data()
        original_count = len(data["slides"])
        data["slides"] = [s for s in data["slides"] if s["id"] != slide_id]
        
        if len(data["slides"]) < original_count:
            self._write_data(data)
            return True
        return False
    
    def reorder_slides(self, slide_ids: list[str]):
        """
        重新排序幻灯片
        
        Args:
            slide_ids: 新的幻灯片 ID 顺序
        """
        data = self._read_data()
        slide_map = {s["id"]: s for s in data["slides"]}
        
        # 按新顺序重新组织
        data["slides"] = [slide_map[sid] for sid in slide_ids if sid in slide_map]
        self._write_data(data)
    
    def reset(self):
        """
        重置项目状态到初始状态（仅用于测试）
        """
        logger.warning("Resetting project to initial state")
        initial_data = {
            "style_reference": None,
            "slides": []
        }
        self._write_data(initial_data)
        logger.info("Project reset complete")
