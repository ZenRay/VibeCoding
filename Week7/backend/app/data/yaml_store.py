"""
YAML 存储层 - 处理 outline.yml 的读写操作（支持版本化）
"""
import yaml
import os
from pathlib import Path
from typing import Optional, List, Dict
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class YAMLStore:
    """YAML 文件存储管理器（支持版本化项目）"""
    
    def __init__(self, version: Optional[int] = None):
        """
        初始化 YAML 存储
        
        Args:
            version: 版本号（可选）
                    - 如果提供，使用 assets/vX/outline.yml
                    - 如果为 None，用于版本管理功能（不绑定特定版本）
        """
        self.base_dir = Path(__file__).parent.parent.parent.parent  # Week7/
        self.assets_dir = self.base_dir / "assets"
        self.version = version
        
        if version is not None:
            # 绑定到特定版本
            self.version_dir = self.assets_dir / f"v{version}"
            self.file_path = self.version_dir / "outline.yml"
            logger.info(f"YAMLStore initialized for version {version}: {self.file_path}")
            self._ensure_file_exists()
        else:
            # 版本管理模式（不绑定特定文件）
            self.version_dir = None
            self.file_path = None
            logger.info("YAMLStore initialized in version management mode")
    
    def _ensure_file_exists(self):
        """确保 YAML 文件存在"""
        if self.file_path is None:
            return
            
        # 确保版本目录存在
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.file_path.exists():
            logger.warning(f"YAML file does not exist, creating: {self.file_path}")
            initial_data = {
                "version": self.version,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "style_reference": None,
                "style_prompt": None,
                "slides": []
            }
            self._write_data(initial_data)
            logger.info(f"Created initial outline.yml for version {self.version}")
        else:
            logger.info(f"YAML file exists: {self.file_path}")
    
    def _read_data(self) -> dict:
        """
        读取 YAML 文件内容
        
        Returns:
            dict: YAML 文件内容
        """
        if self.file_path is None:
            raise RuntimeError("No version bound, cannot read data")
            
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if not data:
                    return {
                        "version": self.version,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "style_reference": None,
                        "style_prompt": None,
                        "slides": []
                    }
                
                # 向后兼容：确保所有字段存在
                if "version" not in data:
                    data["version"] = self.version
                if "created_at" not in data:
                    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if "style_prompt" not in data:
                    data["style_prompt"] = None
                    
                return data
        except yaml.YAMLError as e:
            logger.error(f"YAML parse error: {e}")
            return {
                "version": self.version,
                "style_reference": None,
                "style_prompt": None,
                "slides": []
            }
        except Exception as e:
            logger.exception(f"Error reading YAML: {e}")
            return {
                "version": self.version,
                "style_reference": None,
                "style_prompt": None,
                "slides": []
            }
    
    def _write_data(self, data: dict):
        """
        原子写入 YAML 文件
        
        Args:
            data: 要写入的数据
            
        Raises:
            Exception: 写入失败时抛出异常
        """
        if self.file_path is None:
            raise RuntimeError("No version bound, cannot write data")
            
        try:
            # 确保版本号一致
            data["version"] = self.version
            
            # 原子写入: 先写临时文件,再替换
            temp_path = self.file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
            
            # 替换原文件
            temp_path.replace(self.file_path)
            logger.debug(f"Successfully wrote YAML file for version {self.version}")
        except yaml.YAMLError as e:
            logger.error(f"YAML serialization error: {e}")
            raise
        except Exception as e:
            logger.exception(f"Error writing YAML: {e}")
            raise
    
    # ============ 版本管理功能 ============
    
    def list_versions(self) -> List[int]:
        """
        列出所有可用版本
        
        Returns:
            List[int]: 版本号列表，按降序排列（最新的在前）
        """
        if not self.assets_dir.exists():
            return []
        
        versions = []
        for item in self.assets_dir.iterdir():
            if item.is_dir() and item.name.startswith('v'):
                try:
                    version_num = int(item.name[1:])
                    # 检查是否有 outline.yml
                    if (item / "outline.yml").exists():
                        versions.append(version_num)
                except ValueError:
                    continue
        
        versions.sort(reverse=True)  # 降序：最新的在前
        logger.info(f"Found {len(versions)} versions: {versions}")
        return versions
    
    def get_version_info(self, version: int) -> Optional[Dict]:
        """
        获取版本摘要信息（不加载完整数据）
        
        Args:
            version: 版本号
            
        Returns:
            dict: 版本信息，包含 version, created_at, style_reference, slide_count
                 如果版本不存在返回 None
        """
        version_dir = self.assets_dir / f"v{version}"
        outline_path = version_dir / "outline.yml"
        
        if not outline_path.exists():
            return None
        
        try:
            with open(outline_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            return {
                "version": version,
                "created_at": data.get("created_at"),
                "project_name": data.get("project_name"),
                "style_reference": data.get("style_reference"),
                "style_prompt": data.get("style_prompt"),
                "slide_count": len(data.get("slides", []))
            }
        except Exception as e:
            logger.error(f"Error reading version {version} info: {e}")
            return None
    
    def create_new_version(self, style_prompt: str = None, project_name: str = None) -> int:
        """
        创建新版本目录和 outline.yml
        
        Args:
            style_prompt: 风格描述（可选）
            project_name: 项目名称（可选）
            
        Returns:
            int: 新版本号
        """
        # 找到最大版本号
        existing_versions = self.list_versions()
        new_version = max(existing_versions, default=0) + 1
        
        # 创建版本目录
        version_dir = self.assets_dir / f"v{new_version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建初始 outline.yml
        initial_data = {
            "version": new_version,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_name": project_name,
            "style_reference": None,
            "style_prompt": style_prompt,
            "slides": []
        }
        
        outline_path = version_dir / "outline.yml"
        with open(outline_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(initial_data, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Created new version {new_version} at {version_dir}")
        return new_version
    
    def delete_version(self, version: int) -> bool:
        """
        删除指定版本（危险操作！）
        
        Args:
            version: 版本号
            
        Returns:
            bool: 是否删除成功
        """
        version_dir = self.assets_dir / f"v{version}"
        
        if not version_dir.exists():
            logger.warning(f"Version {version} does not exist")
            return False
        
        try:
            import shutil
            shutil.rmtree(version_dir)
            logger.warning(f"Deleted version {version} at {version_dir}")
            return True
        except Exception as e:
            logger.error(f"Error deleting version {version}: {e}")
            return False
    
    # ============ 原有功能（需要绑定版本）============
    
    def get_project_state(self) -> dict:
        """
        获取完整项目状态
        
        Returns:
            dict: 项目状态 (version, style_reference, slides)
        """
        return self._read_data()
    
    def set_style_reference(self, image_path: str, style_prompt: str = None):
        """
        设置风格参考图片和 prompt
        
        Args:
            image_path: 图片路径
            style_prompt: 风格描述（可选）
            
        Raises:
            Exception: 写入失败时抛出异常
        """
        if not image_path or not image_path.strip():
            raise ValueError("Image path cannot be empty")
        
        logger.info(f"Setting style reference to: {image_path}, prompt: {style_prompt}")
        data = self._read_data()
        data["style_reference"] = image_path.strip()
        if style_prompt is not None:
            data["style_prompt"] = style_prompt
        self._write_data(data)
        logger.info("Style reference and prompt saved successfully")
    
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
            "version": self.version,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "style_reference": None,
            "style_prompt": None,
            "slides": []
        }
        self._write_data(initial_data)
        logger.info("Project reset complete")
