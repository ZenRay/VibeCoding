"""
Google Gemini AI 图片生成器封装
"""
import os
from pathlib import Path
from typing import List
import hashlib
import time
import logging

logger = logging.getLogger(__name__)


class GeminiGenerator:
    """Gemini AI 图片生成器"""
    
    def __init__(self, api_key: str, model: str = "gemini-3-pro-image-preview"):
        """
        初始化生成器
        
        Args:
            api_key: Gemini API Key
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.model = model
        self.assets_dir = Path(__file__).parent.parent.parent.parent / "assets"
        self.assets_dir.mkdir(exist_ok=True)
        
        # 注意: 实际使用时需要导入 google.genai
        # from google import genai
        # from google.genai import types
        # self.client = genai.Client(api_key=api_key)
        
        # 当前为 Stub 模式,用于测试
        if not api_key or api_key == "":
            logger.warning("No Gemini API key provided. Running in stub mode.")
            self.client = None
        else:
            logger.info(f"GeminiGenerator initialized with model: {model}")
            self.client = None  # TODO: 替换为真实客户端
        
        logger.info(f"Assets directory: {self.assets_dir}")
    
    def generate_style_candidates(self, prompt: str) -> List[str]:
        """
        生成风格候选图片
        
        Args:
            prompt: 风格描述提示
        
        Returns:
            List[str]: 生成的 2 张图片路径
            
        Raises:
            ValueError: 输入验证失败
            RuntimeError: API 调用失败
        """
        # 输入验证
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        prompt = prompt.strip()
        logger.info(f"Generating style candidates for prompt: {prompt[:50]}...")
        
        if self.client is None:
            # Stub 模式: 返回模拟路径
            logger.info("Running in stub mode, generating mock paths")
            timestamp = int(time.time())
            paths = [
                str(self.assets_dir / f"style_candidate_1_{timestamp}.png"),
                str(self.assets_dir / f"style_candidate_2_{timestamp}.png")
            ]
            logger.info(f"Generated mock paths: {paths}")
            return paths
        
        # 实际使用 Gemini API 的代码:
        # try:
        #     from google import genai
        #     from google.genai import types
        #     from PIL import Image
        #
        #     images = []
        #     for i in range(2):
        #         logger.info(f"Generating candidate {i+1}/2")
        #         response = self.client.models.generate_content(
        #             model=self.model,
        #             contents=[prompt],
        #         )
        #         
        #         for part in response.parts:
        #             if part.inline_data is not None:
        #                 image = part.as_image()
        #                 prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        #                 timestamp = int(time.time())
        #                 image_path = self.assets_dir / f"style_{prompt_hash}_{i}_{timestamp}.png"
        #                 image.save(image_path)
        #                 images.append(str(image_path))
        #                 logger.info(f"Saved image to: {image_path}")
        #                 break
        #     
        #     if len(images) != 2:
        #         raise RuntimeError(f"Expected 2 images, got {len(images)}")
        #     
        #     return images
        # except Exception as e:
        #     logger.exception(f"Failed to generate style candidates: {e}")
        #     raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def generate_slide_image(self, text: str, style_ref_path: str) -> str:
        """
        生成幻灯片图片 (使用风格参考)
        
        Args:
            text: 幻灯片文本
            style_ref_path: 风格参考图片路径
        
        Returns:
            str: 生成的图片路径
            
        Raises:
            ValueError: 输入验证失败
            RuntimeError: API 调用失败
        """
        # 输入验证
        if not text or not text.strip():
            raise ValueError("Slide text cannot be empty")
        if not style_ref_path or not style_ref_path.strip():
            raise ValueError("Style reference path cannot be empty")
        
        text = text.strip()
        logger.info(f"Generating slide image for text: {text[:50]}...")
        
        if self.client is None:
            # Stub 模式
            content_hash = hashlib.md5(text.encode()).hexdigest()
            path = str(self.assets_dir / f"slide_{content_hash}.png")
            logger.info(f"Generated mock slide path: {path}")
            return path
        
        # 实际使用 Gemini API 的代码:
        # try:
        #     prompt = f"Create a slide image with the following text: {text}. Use this style reference."
        #     logger.info(f"Using style reference: {style_ref_path}")
        #     
        #     # 注意: 需要传递 style_ref_path 作为参考图片
        #     response = self.client.models.generate_content(
        #         model=self.model,
        #         contents=[prompt],
        #         # config 中可能需要传递风格参考图片
        #     )
        #
        #     for part in response.parts:
        #         if part.inline_data is not None:
        #             image = part.as_image()
        #             content_hash = hashlib.md5(text.encode()).hexdigest()
        #             timestamp = int(time.time())
        #             image_path = self.assets_dir / f"slide_{content_hash}_{timestamp}.png"
        #             image.save(image_path)
        #             logger.info(f"Saved slide image to: {image_path}")
        #             return str(image_path)
        #     
        #     raise RuntimeError("No image data in response")
        # except Exception as e:
        #     logger.exception(f"Failed to generate slide image: {e}")
        #     raise RuntimeError(f"Gemini API error: {str(e)}")
