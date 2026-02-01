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
    
    def __init__(self, api_key: str, model: str = "gemini-3-pro-image-preview", mode: str = "stub", yaml_store=None, provider: str = "google", openrouter_api_key: str = "", openrouter_model: str = "", image_size: str = "1K", image_aspect_ratio: str = "16:9", version: int = None):
        """
        初始化生成器
        
        Args:
            api_key: Gemini API Key (用于 Google provider)
            model: 使用的模型名称 (用于 Google provider)
            mode: 运行模式 - "stub" (占位符) 或 "real" (真实AI)
            yaml_store: YAMLStore 实例，用于读取 outline.yml
            provider: AI provider - "google" 或 "openrouter"
            openrouter_api_key: OpenRouter API Key (用于 OpenRouter provider)
            openrouter_model: OpenRouter 模型名称
            image_size: 图片分辨率 - "1K", "2K", "4K"
            image_aspect_ratio: 图片纵横比 - "16:9", "4:3", "1:1"
            version: 版本号（如果提供，直接使用；否则从 yaml_store 推断）
        """
        self.api_key = api_key
        self.model = model
        self.mode = mode
        self.yaml_store = yaml_store
        self.provider = provider
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_model = openrouter_model
        self.image_size = image_size
        self.image_aspect_ratio = image_aspect_ratio
        self.base_assets_dir = Path(__file__).parent.parent.parent.parent / "assets"
        self.base_assets_dir.mkdir(exist_ok=True)
        
        # 版本管理：如果提供了版本号，直接使用；否则从 yaml_store 推断
        if version is not None:
            self.current_version = version
            self.assets_dir = self.base_assets_dir / f"v{version}"
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"GeminiGenerator bound to version {version}")
        else:
            # 旧模式：延迟到实际生成时确定版本号
            self.current_version = None
            self.assets_dir = None
            logger.warning("GeminiGenerator initialized without version (legacy mode)")
        
        logger.info(f"Image config: size={image_size}, aspect_ratio={image_aspect_ratio}")
        
        # 根据模式和 provider 初始化客户端
        if mode == "real":
            if provider == "openrouter" and openrouter_api_key:
                self._init_openrouter()
            elif provider == "google" and api_key:
                self._init_google()
            else:
                self.client = None
                logger.warning(f"No valid API key for provider '{provider}'. Running in STUB mode.")
                self.mode = "stub"
        else:
            self.client = None
            if mode == "stub":
                logger.info("✓ GeminiGenerator initialized in STUB mode (using placeholders)")
            else:
                logger.warning(f"No API key provided. Running in STUB mode.")
        
        logger.info(f"Base assets directory: {self.base_assets_dir}")
    
    def _init_google(self):
        """初始化 Google Gemini 客户端"""
        try:
            from google import genai
            import os
            os.environ['GOOGLE_API_KEY'] = self.api_key
            self.client = genai.Client()
            logger.info(f"✓ GeminiGenerator initialized with Google provider (model: {self.model})")
        except ImportError as e:
            logger.error(f"google-genai package not installed: {e}")
            logger.error("Run: pip install google-genai")
            logger.warning("Falling back to STUB mode")
            self.mode = "stub"
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini client: {e}")
            logger.warning("Falling back to STUB mode")
            self.mode = "stub"
            self.client = None
    
    def _init_openrouter(self):
        """初始化 OpenRouter 客户端"""
        try:
            import httpx
            import os
            
            # OpenRouter 使用 HTTPS，临时禁用代理以避免 SSL 错误
            # httpx 会自动从环境变量读取代理，所以需要临时清除
            original_http_proxy = os.environ.pop('HTTP_PROXY', None)
            original_https_proxy = os.environ.pop('HTTPS_PROXY', None)
            original_http_proxy_lower = os.environ.pop('http_proxy', None)
            original_https_proxy_lower = os.environ.pop('https_proxy', None)
            
            self.client = httpx.Client(
                base_url="https://openrouter.ai/api/v1",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": "https://github.com/vibecoding/ai-slide-generator",
                    "X-Title": "AI Slide Generator"
                },
                timeout=60.0
            )
            
            # 恢复原始代理设置（用于其他可能需要代理的请求，如 Google API）
            if original_http_proxy:
                os.environ['HTTP_PROXY'] = original_http_proxy
            if original_https_proxy:
                os.environ['HTTPS_PROXY'] = original_https_proxy
            if original_http_proxy_lower:
                os.environ['http_proxy'] = original_http_proxy_lower
            if original_https_proxy_lower:
                os.environ['https_proxy'] = original_https_proxy_lower
            
            logger.info(f"✓ GeminiGenerator initialized with OpenRouter provider (model: {self.openrouter_model})")
            logger.info(f"  Proxy bypassed for OpenRouter to avoid SSL errors")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter client: {e}")
            logger.warning("Falling back to STUB mode")
            self.mode = "stub"
            self.client = None
    
    def _get_or_create_version(self) -> int:
        """
        获取当前版本号
        
        如果已绑定版本，直接返回；否则报错（新模式下必须绑定版本）
        
        Returns:
            int: 当前版本号（如 1, 2, 3）
            
        Raises:
            RuntimeError: 如果未绑定版本
        """
        if self.current_version is None:
            raise RuntimeError("Generator not bound to a version. Please initialize with version parameter.")
        
        return self.current_version
        
        return self.current_version
    
    # 移除 assets_dir 属性（现在在 __init__ 中直接设置）
    
    def _init_google(self):
        """获取当前版本的 assets 目录"""
        version = self._get_or_create_version()
        return self.base_assets_dir / f"v{version}"
    
    def _generate_image_google(self, prompt: str):
        """使用 Google Gemini API 生成图像"""
        from google import genai
        from google.genai import types
        from PIL import Image
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="2K",
                )
            ),
        )
        
        # 根据文档，图片在 response.parts 中以 inline_data 形式返回
        for part in response.parts:
            if part.inline_data is not None:
                # 使用 as_image() 方法获取 PIL Image
                return part.as_image()
        
        raise RuntimeError("No image found in Google API response")
    
    def _generate_image_openrouter(self, prompt: str):
        """使用 OpenRouter API 生成图像（带重试）"""
        import base64
        import io
        import time
        from PIL import Image
        
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[OpenRouter] Attempt {attempt + 1}/{max_retries}: Sending request with prompt: {prompt[:100]}...")
                
                response = self.client.post(
                    "/chat/completions",
                    json={
                        "model": self.openrouter_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt}
                                ]
                            }
                        ],
                        "modalities": ["image", "text"],  # 关键：指定要生成图像
                        "image_config": {  # Gemini 模型配置
                            "aspect_ratio": "16:9",  # 1344x768
                            "image_size": "2K"       # 2K 分辨率
                        }
                    }
                )
                
                logger.info(f"[OpenRouter] Response status: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"[OpenRouter] Error response: {response.text}")
                    if attempt < max_retries - 1:
                        logger.warning(f"[OpenRouter] Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    raise RuntimeError(f"OpenRouter API error: {response.status_code} - {response.text}")
                
                data = response.json()
                logger.info(f"[OpenRouter] Response keys: {list(data.keys())}")
                
                # 解析响应中的图像
                if 'choices' not in data or len(data['choices']) == 0:
                    logger.error(f"[OpenRouter] No choices in response: {data}")
                    if attempt < max_retries - 1:
                        logger.warning(f"[OpenRouter] Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        continue
                    raise RuntimeError("No choices in OpenRouter response")
                
                message = data['choices'][0]['message']
                logger.info(f"[OpenRouter] Message keys: {list(message.keys())}")
                
                # 检查 images 字段（OpenRouter 特有）
                if 'images' in message and message['images']:
                    images_list = message['images']
                    logger.info(f"[OpenRouter] Found {len(images_list)} images")
                    logger.info(f"[OpenRouter] First image type: {type(images_list[0])}")
                    logger.info(f"[OpenRouter] First image data: {str(images_list[0])[:200]}...")
                    
                    # 取第一张图像
                    image_data = images_list[0]
                    
                    # 如果是字典，提取 URL
                    if isinstance(image_data, dict):
                        logger.info(f"[OpenRouter] Image dict keys: {list(image_data.keys())}")
                        # OpenRouter 格式: {'type': 'image_url', 'image_url': {'url': 'data:...'}}
                        image_url_obj = image_data.get('image_url') or image_data.get('url') or image_data.get('data')
                        if isinstance(image_url_obj, dict):
                            image_url = image_url_obj.get('url')
                        else:
                            image_url = image_url_obj
                        
                        if not image_url:
                            logger.error(f"[OpenRouter] Cannot find URL in dict. Full dict: {image_data}")
                            if attempt < max_retries - 1:
                                logger.warning(f"[OpenRouter] Retrying in {retry_delay}s...")
                                time.sleep(retry_delay)
                                continue
                            raise RuntimeError(f"Cannot find image URL in dict: {list(image_data.keys())}")
                    else:
                        image_url = image_data
                    
                    logger.info(f"[OpenRouter] Image URL type: {type(image_url)}")
                    logger.info(f"[OpenRouter] Image URL prefix: {str(image_url)[:50]}...")
                    
                    # 处理 base64 编码的图像
                    if image_url.startswith('data:image'):
                        logger.info("[OpenRouter] Processing base64 image")
                        base64_data = image_url.split(',', 1)[1]
                        image_bytes = base64.b64decode(base64_data)
                        logger.info(f"[OpenRouter] Decoded {len(image_bytes)} bytes")
                        img = Image.open(io.BytesIO(image_bytes))
                        logger.info(f"[OpenRouter] Image size: {img.size}, mode: {img.mode}")
                        return img
                    else:
                        # 如果是 URL，下载图像
                        logger.info(f"[OpenRouter] Downloading from URL: {image_url}")
                        import httpx
                        img_response = httpx.get(image_url, timeout=30)
                        logger.info(f"[OpenRouter] Download status: {img_response.status_code}")
                        img = Image.open(io.BytesIO(img_response.content))
                        logger.info(f"[OpenRouter] Image size: {img.size}, mode: {img.mode}")
                        return img
                
                # 备用：检查 content 列表格式
                logger.warning("[OpenRouter] No images field, checking content format")
                content = message.get('content')
                logger.info(f"[OpenRouter] Content type: {type(content)}")
                
                if isinstance(content, list):
                    logger.info(f"[OpenRouter] Content list length: {len(content)}")
                    for i, content_item in enumerate(content):
                        logger.info(f"[OpenRouter] Content[{i}] type: {type(content_item)}")
                        if isinstance(content_item, dict):
                            logger.info(f"[OpenRouter] Content[{i}] keys: {list(content_item.keys())}")
                            if content_item.get('type') == 'image_url':
                                image_url = content_item['image_url']['url']
                                logger.info(f"[OpenRouter] Found image_url in content[{i}]")
                                
                                if image_url.startswith('data:image'):
                                    base64_data = image_url.split(',', 1)[1]
                                    image_bytes = base64.b64decode(base64_data)
                                    return Image.open(io.BytesIO(image_bytes))
                                else:
                                    import httpx
                                    img_response = httpx.get(image_url, timeout=30)
                                    return Image.open(io.BytesIO(img_response.content))
                
                # 如果都没找到图像，重试
                logger.warning(f"[OpenRouter] No image found in response (attempt {attempt + 1}/{max_retries})")
                logger.warning(f"[OpenRouter] Message structure: {message}")
                
                if attempt < max_retries - 1:
                    logger.warning(f"[OpenRouter] Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"[OpenRouter] Failed after {max_retries} attempts. Message structure: {message}")
                    raise RuntimeError(f"No image found in OpenRouter response after {max_retries} attempts")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"[OpenRouter] Error on attempt {attempt + 1}: {e}")
                    logger.warning(f"[OpenRouter] Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"[OpenRouter] Failed after {max_retries} attempts: {e}")
                    raise
    
    def _generate_image_with_style_google(self, prompt: str, style_image):
        """使用 Google Gemini API 生成带风格参考的图像"""
        from google import genai
        from google.genai import types
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[style_image, prompt],  # 先传风格图像，再传 prompt
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9",
                    image_size="2K",
                )
            ),
        )
        
        for part in response.parts:
            if part.inline_data is not None:
                return part.as_image()
        
        raise RuntimeError("No image found in Google API response")
    
    def _generate_image_with_style_openrouter(self, prompt: str, style_image):
        """使用 OpenRouter API 生成带风格参考的图像"""
        import base64
        import io
        from PIL import Image
        
        # 将风格参考图像转换为 base64
        img_byte_arr = io.BytesIO()
        style_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
        
        response = self.client.post(
            "/chat/completions",
            json={
                "model": self.openrouter_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            },
                            {"type": "text", "text": prompt}  # 先图像后文本，符合 "image above" 语义
                        ]
                    }
                ],
                "modalities": ["image", "text"],
                "image_config": {  # Gemini 模型配置
                    "aspect_ratio": self.image_aspect_ratio,
                    "image_size": self.image_size
                }
            }
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"OpenRouter API error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # 解析响应（与 _generate_image_openrouter 相同的逻辑）
        if 'choices' not in data or len(data['choices']) == 0:
            raise RuntimeError("No choices in OpenRouter response")
        
        message = data['choices'][0]['message']
        
        # 检查 images 字段（OpenRouter 特有）
        if 'images' in message and message['images']:
            images_list = message['images']
            logger.info(f"Found {len(images_list)} images in response")
            
            image_data = images_list[0]
            
            # 如果是字典，提取 URL
            if isinstance(image_data, dict):
                # OpenRouter 格式: {'type': 'image_url', 'image_url': {'url': 'data:...'}}
                image_url_obj = image_data.get('image_url') or image_data.get('url') or image_data.get('data')
                if isinstance(image_url_obj, dict):
                    image_url = image_url_obj.get('url')
                else:
                    image_url = image_url_obj
                
                if not image_url:
                    raise RuntimeError(f"Cannot find image URL in dict: {list(image_data.keys())}")
            else:
                image_url = image_data
            
            if image_url.startswith('data:image'):
                base64_data = image_url.split(',', 1)[1]
                image_bytes = base64.b64decode(base64_data)
                return Image.open(io.BytesIO(image_bytes))
            else:
                import httpx
                img_response = httpx.get(image_url, timeout=30)
                return Image.open(io.BytesIO(img_response.content))
        
        # 备用：检查 content 列表格式
        content = message.get('content')
        if isinstance(content, list):
            for content_item in content:
                if isinstance(content_item, dict) and content_item.get('type') == 'image_url':
                    image_url = content_item['image_url']['url']
                    
                    if image_url.startswith('data:image'):
                        base64_data = image_url.split(',', 1)[1]
                        image_bytes = base64.b64decode(base64_data)
                        return Image.open(io.BytesIO(image_bytes))
                    else:
                        import httpx
                        img_response = httpx.get(image_url, timeout=30)
                        return Image.open(io.BytesIO(img_response.content))
        
        raise RuntimeError("No image found in OpenRouter response")
    
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
        
        if self.mode == "stub" or self.client is None:
            # Stub 模式: 返回相对路径（相对于 API 根路径）
            logger.info("Running in stub mode, generating mock paths")
            version = self._get_or_create_version()
            timestamp = int(time.time())
            paths = [
                f"assets/v{version}/style_candidate_1_{timestamp}.png",
                f"assets/v{version}/style_candidate_2_{timestamp}.png"
            ]
            logger.info(f"Generated mock paths: {paths}")
            
            # 在 Stub 模式下创建占位符图片
            from PIL import Image, ImageDraw, ImageFont
            for i, path in enumerate(paths):
                full_path = self.base_assets_dir / Path(path).relative_to("assets")
                if not full_path.exists():
                    # 创建一个简单的占位符图片
                    img = Image.new('RGB', (800, 600), color=(100 + i*50, 100 + i*30, 200))
                    draw = ImageDraw.Draw(img)
                    text = f"Style Candidate {i+1}\n{prompt[:30]}..."
                    draw.text((400, 300), text, fill=(255, 255, 255), anchor="mm")
                    img.save(full_path)
                    logger.info(f"Created placeholder image: {full_path}")
            
            return paths
        
        # 实际使用 AI API 的代码
        try:
            version = self._get_or_create_version()
            images = []
            
            # 优化风格候选的 prompt
            style_prompt = f"Generate an artistic image showcasing the '{prompt}' style. This image will be used as a style reference for subsequent image generation. Make it visually distinctive and representative of this style."
            
            for i in range(2):
                logger.info(f"[StyleGen] Generating candidate {i+1}/2 with {self.provider.upper()} AI...")
                
                # 为每个候选添加变化，确保多样性
                varied_prompt = f"{style_prompt} (variation {i + 1}, make it unique)"
                
                if self.provider == "openrouter":
                    image = self._generate_image_openrouter(varied_prompt)
                else:  # google
                    image = self._generate_image_google(varied_prompt)
                
                logger.info(f"[StyleGen] Image {i+1} generated successfully: {image.size}, {image.mode}")
                
                # 保存图片
                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
                timestamp = int(time.time())
                filename = f"style_{prompt_hash}_{i}_{timestamp}.png"
                full_path = self.assets_dir / filename
                
                logger.info(f"[StyleGen] Saving image to: {full_path}")
                image.save(full_path)
                
                relative_path = f"assets/v{version}/{filename}"
                images.append(relative_path)
                logger.info(f"[StyleGen] ✓ Saved image {i+1}: {relative_path}")
            
            if len(images) != 2:
                raise RuntimeError(f"Expected 2 images, got {len(images)}")
            
            logger.info(f"[StyleGen] All images generated successfully: {images}")
            return images
        except Exception as e:
            logger.exception(f"Failed to generate style candidates: {e}")
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
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
        
        if self.mode == "stub" or self.client is None:
            # Stub 模式: 返回相对路径
            version = self._get_or_create_version()
            content_hash = hashlib.md5(text.encode()).hexdigest()
            path = f"assets/v{version}/slide_{content_hash}.png"
            logger.info(f"Generated mock slide path: {path}")
            
            # 在 Stub 模式下创建占位符图片
            from PIL import Image, ImageDraw
            full_path = self.base_assets_dir / Path(path).relative_to("assets")
            if not full_path.exists():
                # 创建一个简单的占位符图片
                img = Image.new('RGB', (1200, 800), color=(80, 120, 180))
                draw = ImageDraw.Draw(img)
                # 绘制文本（简单版本）
                lines = text.split('\n')[:5]  # 最多5行
                y = 200
                for line in lines:
                    draw.text((600, y), line[:50], fill=(255, 255, 255), anchor="mm")
                    y += 100
                img.save(full_path)
                logger.info(f"Created placeholder slide image: {full_path}")
            
            return path
        
        # 实际使用 AI API 的代码
        try:
            from PIL import Image as PILImage
            
            version = self._get_or_create_version()
            
            # 日志：记录输入文本的详细信息（用于调试编码问题）
            logger.info(f"[SlideGen] Input text preview: {text[:100]}")
            logger.info(f"[SlideGen] Text encoding: {text.encode('utf-8')[:200]}")
            logger.info(f"[SlideGen] Text length: {len(text)} characters")
            
            # v7.2 - 强化风格引用，明确要求模仿参考图片
            prompt_text = (
                f"🎨 STYLE REFERENCE: The image shown above is your STYLE GUIDE.\n"
                f"You MUST mimic its visual style (colors, fonts, layout, aesthetic) while displaying the text below.\n\n"
                
                f"=== EXACT TEXT (RENDER PRECISELY) ===\n"
                f"{text}\n"
                f"=== END TEXT ===\n\n"
                
                f"⚠️ CRITICAL RULES:\n"
                f"1. STYLE MATCHING (HIGHEST PRIORITY):\n"
                f"   - Use the SAME color palette as the reference image above\n"
                f"   - Use the SAME font style (handwritten/modern/tech/etc.)\n"
                f"   - Use the SAME background style (gradient/solid/pattern)\n"
                f"   - Use the SAME visual aesthetic (minimalist/vibrant/corporate)\n"
                f"   - The output should look like it belongs to the SAME design system\n\n"
                
                f"2. TEXT ACCURACY (SECOND PRIORITY):\n"
                f"   - Display EVERY character EXACTLY as provided above\n"
                f"   - DO NOT add content that is not in the input\n"
                f"   - DO NOT create additional sections or diagrams\n"
                f"   - Use professional Chinese fonts (Noto Sans CJK, PingFang)\n\n"
                
                f"3. STRUCTURE PARSING:\n"
                f"   If text starts with '标题: X':\n"
                f"     → Display 'X' as main title (large, 60-70pt, centered at top)\n"
                f"   \n"
                f"   For remaining text:\n"
                f"     → If it's a simple sentence: Display as subtitle/body text (32-40pt, centered)\n"
                f"     → If it contains ASCII art (╔═╗ ┌─┐): Convert to visual cards\n"
                f"     → If it contains bullets (•, -): Format as list\n\n"
                
                f"4. WHAT NOT TO DO:\n"
                f"   ❌ DO NOT invent additional content\n"
                f"   ❌ DO NOT create complex diagrams if input is simple\n"
                f"   ❌ DO NOT add decorative cards with unrelated text\n"
                f"   ❌ DO NOT translate or paraphrase\n"
                f"   ❌ DO NOT ignore the reference image style\n\n"
                
                f"✅ GOAL: Create a slide that looks EXACTLY like the reference image in style, but displays the provided text.\n"
            )
            logger.info(f"Using style reference: {style_ref_path}")
            logger.info(f"Generating slide image with {self.provider.upper()} AI...")
            
            # 加载风格参考图片
            style_ref_full_path = self.base_assets_dir / Path(style_ref_path).relative_to("assets")
            style_image = PILImage.open(style_ref_full_path)
            
            # 根据 provider 生成图像
            if self.provider == "openrouter":
                image = self._generate_image_with_style_openrouter(prompt_text, style_image)
            else:  # google
                image = self._generate_image_with_style_google(prompt_text, style_image)
            
            # 保存图片
            content_hash = hashlib.md5(text.encode()).hexdigest()
            timestamp = int(time.time())
            filename = f"slide_{content_hash}_{timestamp}.png"
            full_path = self.assets_dir / filename
            image.save(full_path)
            relative_path = f"assets/v{version}/{filename}"
            logger.info(f"✓ Saved slide image to: {full_path}")
            
            return relative_path
            
            raise RuntimeError("No image data in response")
        except Exception as e:
            logger.exception(f"Failed to generate slide image: {e}")
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def _add_styled_text_overlay(self, base_image, title: str, content: str):
        """
        在基础布局图上添加带风格的文本
        
        Args:
            base_image: AI 生成的布局背景图
            title: 标题文本
            content: 内容文本
            
        Returns:
            添加文本后的图片
        """
        from PIL import ImageDraw, ImageFont
        import textwrap
        
        # 创建可编辑的图层
        img = base_image.copy()
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        logger.info(f"[TextOverlay] Image size: {width}x{height}")
        logger.info(f"[TextOverlay] Title: {title[:50] if title else 'None'}")
        
        # 尝试加载中文字体
        try:
            # Linux 系统常见中文字体路径
            font_paths = [
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Ubuntu
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",      # Noto Sans CJK
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",              # 文泉驿微米黑
                "/System/Library/Fonts/PingFang.ttc",                          # macOS
                "C:\\Windows\\Fonts\\msyh.ttc",                                 # Windows 微软雅黑
            ]
            
            font_title = None
            font_content = None
            
            for font_path in font_paths:
                try:
                    font_title = ImageFont.truetype(font_path, 64)
                    font_content = ImageFont.truetype(font_path, 24)
                    logger.info(f"[TextOverlay] Loaded font: {font_path}")
                    break
                except:
                    continue
            
            if not font_title:
                logger.warning("[TextOverlay] No TrueType font found, using default")
                font_title = ImageFont.load_default()
                font_content = ImageFont.load_default()
        except Exception as e:
            logger.warning(f"[TextOverlay] Font loading failed: {e}, using default")
            font_title = ImageFont.load_default()
            font_content = ImageFont.load_default()
        
        # 1. 渲染标题（带风格）
        if title:
            # 标题位置：顶部居中
            title_y = int(height * 0.08)
            
            # 方法1：渲染阴影文字（立体效果）
            shadow_offset = 3
            # 阴影（深色）
            title_bbox = draw.textbbox((0, 0), title, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            
            draw.text((title_x + shadow_offset, title_y + shadow_offset), 
                     title, font=font_title, fill=(100, 100, 100, 180))
            
            # 主文字（深色，带渐变效果的近似）
            draw.text((title_x, title_y), 
                     title, font=font_title, fill=(40, 40, 40, 255))
            
            logger.info(f"[TextOverlay] Title rendered at ({title_x}, {title_y})")
        
        # 2. 解析并渲染内容（简化版 - 只处理关键信息）
        if content:
            # 提取主要章节标题（╔══╗ 或 ┌──┐ 包围的内容）
            import re
            
            # 查找所有章节标题（双线框）
            section_pattern = r'║\s*([^║\n]+?)\s*║'
            sections = re.findall(section_pattern, content)
            
            if sections:
                # 在卡片区域渲染章节标题
                start_y = int(height * 0.25)
                card_width = int(width * 0.28)
                card_spacing = int(width * 0.05)
                cards_per_row = 3
                
                for idx, section_title in enumerate(sections[:9]):  # 最多9个卡片
                    row = idx // cards_per_row
                    col = idx % cards_per_row
                    
                    card_x = int(width * 0.05) + col * (card_width + card_spacing)
                    card_y = start_y + row * int(height * 0.22)
                    
                    # 章节标题（带风格：阴影 + 深色文字）
                    section_clean = section_title.strip()
                    
                    # 阴影
                    draw.text((card_x + 22, card_y + 22), 
                             section_clean, font=font_content, fill=(120, 120, 120, 150))
                    # 主文字
                    draw.text((card_x + 20, card_y + 20), 
                             section_clean, font=font_content, fill=(30, 30, 30, 255))
                
                logger.info(f"[TextOverlay] Rendered {len(sections[:9])} section titles")
        
        return img
