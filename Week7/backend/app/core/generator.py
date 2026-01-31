"""
Google Gemini AI 图片生成器封装
"""
import os
from pathlib import Path
from typing import List
import hashlib
import time


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
        self.client = None
    
    def generate_style_candidates(self, prompt: str) -> List[str]:
        """
        生成风格候选图片
        
        Args:
            prompt: 风格描述提示
        
        Returns:
            List[str]: 生成的 2 张图片路径
        """
        if self.client is None:
            # Stub 模式: 返回模拟路径
            return [
                str(self.assets_dir / f"style_candidate_1_{int(time.time())}.png"),
                str(self.assets_dir / f"style_candidate_2_{int(time.time())}.png")
            ]
        
        # 实际使用 Gemini API 的代码:
        # from google import genai
        # from google.genai import types
        # from PIL import Image
        #
        # images = []
        # for i in range(2):
        #     response = self.client.models.generate_content(
        #         model=self.model,
        #         contents=[prompt],
        #     )
        #     
        #     for part in response.parts:
        #         if part.inline_data is not None:
        #             image = part.as_image()
        #             image_path = self.assets_dir / f"style_{hashlib.md5(prompt.encode()).hexdigest()}_{i}.png"
        #             image.save(image_path)
        #             images.append(str(image_path))
        # 
        # return images
    
    def generate_slide_image(self, text: str, style_ref_path: str) -> str:
        """
        生成幻灯片图片 (使用风格参考)
        
        Args:
            text: 幻灯片文本
            style_ref_path: 风格参考图片路径
        
        Returns:
            str: 生成的图片路径
        """
        if self.client is None:
            # Stub 模式
            content_hash = hashlib.md5(text.encode()).hexdigest()
            return str(self.assets_dir / f"slide_{content_hash}.png")
        
        # 实际使用 Gemini API 的代码:
        # prompt = f"Create a slide image with the following text: {text}. Use this style reference."
        # # 注意: 需要传递 style_ref_path 作为参考图片
        # response = self.client.models.generate_content(
        #     model=self.model,
        #     contents=[prompt],
        #     # config 中可能需要传递风格参考图片
        # )
        #
        # for part in response.parts:
        #     if part.inline_data is not None:
        #         image = part.as_image()
        #         content_hash = hashlib.md5(text.encode()).hexdigest()
        #         image_path = self.assets_dir / f"slide_{content_hash}.png"
        #         image.save(image_path)
        #         return str(image_path)
