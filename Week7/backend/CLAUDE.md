# Week7 Backend Development Guidelines

**Project**: AI Slide Generator Backend
**Technology Stack**: Python 3.12+, FastAPI, Google Gemini API
**Package Manager**: uv
**Virtual Environment**: `.venv` (managed by uv)

---

## Architecture Principles

### SOLID Principles
- **Single Responsibility**: Each module has one well-defined purpose
  - `api/`: HTTP endpoint definitions only
  - `core/`: Business logic and orchestration
  - `services/`: External service integrations (Gemini API)
  - `storage/`: File system operations (YAML, images)
  - `models/`: Data structures and validation

- **Open/Closed**: Extend functionality through composition, not modification
  - Use dependency injection for services
  - Define clear interfaces (Protocol classes)

- **Liskov Substitution**: Abstract interfaces for swappable implementations
  - Storage backends can be swapped (file system, cloud storage)
  - AI providers can be replaced (Gemini, OpenAI, etc.)

- **Interface Segregation**: Focused, minimal interfaces
  - Separate read and write operations
  - Split large services into focused components

- **Dependency Inversion**: Depend on abstractions, not concrete implementations
  - Use Protocol classes for service contracts
  - Inject dependencies through constructors

### YAGNI (You Aren't Gonna Need It)
- Implement only requested features
- No premature optimization
- No speculative abstractions
- Build the simplest solution that works

### KISS (Keep It Simple, Stupid)
- Prefer simple, readable code over clever solutions
- Avoid deep inheritance hierarchies
- Use standard library when possible
- Clear naming over comments

### DRY (Don't Repeat Yourself)
- Extract common logic into utilities
- Use configuration for environment-specific values
- Reuse validation logic through Pydantic models

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API layer (HTTP endpoints)
│   │   ├── __init__.py
│   │   ├── routes.py           # Route definitions
│   │   └── dependencies.py     # FastAPI dependencies
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration management
│   │   └── slideshow.py        # Slideshow orchestration logic
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── outline.py          # Outline data model (Pydantic)
│   │   ├── slide.py            # Slide data model
│   │   └── style.py            # Style configuration model
│   ├── services/               # External service integrations
│   │   ├── __init__.py
│   │   ├── gemini.py           # Google Gemini API client
│   │   └── image_generator.py  # Image generation service
│   ├── storage/                # Storage layer
│   │   ├── __init__.py
│   │   ├── outline_store.py    # YAML file operations
│   │   └── image_store.py      # Image file operations
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── hash.py             # Content hashing
│       └── logging.py          # Logging configuration
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── config/                     # Configuration files
│   ├── .env.example            # Environment variables template
│   └── logging.yaml            # Logging configuration
├── logs/                       # Application logs (gitignored)
├── data/                       # Runtime data (gitignored)
│   ├── outlines/               # YAML outline files
│   ├── images/                 # Generated images
│   └── styles/                 # User style reference images
├── .venv/                      # Virtual environment (gitignored)
├── pyproject.toml              # Project metadata and dependencies
├── uv.lock                     # Dependency lock file
└── CLAUDE.md                   # This file
```

---

## Code Organization

### Layer Responsibilities

1. **API Layer** (`app/api/`)
   - Request/response handling
   - Input validation (via Pydantic)
   - HTTP status codes and error responses
   - CORS configuration
   - **No business logic**

2. **Core Layer** (`app/core/`)
   - Business logic orchestration
   - Workflow coordination
   - Configuration management
   - **No HTTP concerns**

3. **Service Layer** (`app/services/`)
   - External API integrations
   - Image generation logic
   - Retry logic and error handling
   - **No business rules**

4. **Storage Layer** (`app/storage/`)
   - File I/O operations
   - Data serialization/deserialization
   - Path management
   - **No business logic**

5. **Models Layer** (`app/models/`)
   - Pydantic models for validation
   - Type definitions
   - Data transformation logic
   - **No I/O operations**

### Module Boundaries

- **API cannot call Storage directly** - must go through Core
- **Services are stateless** - no shared mutable state
- **Storage abstracts file system** - other layers use storage interfaces
- **Models are pure data** - no dependencies on other layers

---

## Best Practices

### Python Style (PEP 8 + Modern Practices)

```python
# Good: Type hints everywhere
async def generate_image(
    prompt: str,
    style_image: Path | None = None,
    *,
    model: str = "gemini-3-pro-image-preview"
) -> bytes:
    """Generate image using Gemini API.

    Args:
        prompt: Text description for image generation
        style_image: Optional reference image for style consistency
        model: Gemini model identifier

    Returns:
        Generated image as bytes

    Raises:
        GeminiAPIError: If API call fails
        ValueError: If prompt is empty
    """
    ...

# Good: Use Pydantic for validation
from pydantic import BaseModel, Field, field_validator

class SlideOutline(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    order: int = Field(..., ge=0)
    content_hash: str | None = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v

# Good: Use Protocol for interfaces
from typing import Protocol

class ImageStore(Protocol):
    async def save(self, image_data: bytes, filename: str) -> Path: ...
    async def load(self, filename: str) -> bytes: ...
    async def delete(self, filename: str) -> None: ...

# Good: Dependency injection
class SlideshowService:
    def __init__(
        self,
        image_generator: ImageGenerator,
        outline_store: OutlineStore,
        image_store: ImageStore,
    ) -> None:
        self._image_gen = image_generator
        self._outline_store = outline_store
        self._image_store = image_store
```

### FastAPI Patterns

```python
# Good: Use dependency injection
from fastapi import Depends, FastAPI, HTTPException
from typing import Annotated

app = FastAPI()

def get_slideshow_service() -> SlideshowService:
    # Construct dependencies
    return SlideshowService(...)

SlideshowServiceDep = Annotated[SlideshowService, Depends(get_slideshow_service)]

@app.post("/api/slides/generate")
async def generate_slide(
    request: GenerateSlideRequest,
    service: SlideshowServiceDep,
) -> GenerateSlideResponse:
    try:
        image_path = await service.generate_slide(
            prompt=request.prompt,
            style_image=request.style_image_path,
        )
        return GenerateSlideResponse(image_path=str(image_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GeminiAPIError as e:
        raise HTTPException(status_code=502, detail="Image generation failed")

# Good: Use Pydantic models for request/response
class GenerateSlideRequest(BaseModel):
    prompt: str
    style_image_path: Path | None = None

class GenerateSlideResponse(BaseModel):
    image_path: str
    content_hash: str
```

---

## Concurrency

### Async/Await Best Practices

```python
# Good: Use async for I/O operations
async def generate_slide(prompt: str) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
        return response.content

# Good: Concurrent operations with asyncio.gather
async def generate_all_slides(slides: list[Slide]) -> list[bytes]:
    tasks = [generate_slide(slide.prompt) for slide in slides]
    return await asyncio.gather(*tasks)

# Good: Use asyncio.Semaphore for rate limiting
class GeminiClient:
    def __init__(self, max_concurrent: int = 5):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def generate_image(self, prompt: str) -> bytes:
        async with self._semaphore:
            # Only 5 concurrent requests
            return await self._make_request(prompt)

# Bad: Blocking calls in async functions
async def bad_example():
    time.sleep(1)  # ❌ Blocks event loop

# Good: Use asyncio equivalents
async def good_example():
    await asyncio.sleep(1)  # ✅ Non-blocking
```

### Thread Safety

- **Use asyncio primitives** (`asyncio.Lock`, not `threading.Lock`)
- **Avoid shared mutable state** - prefer immutable data structures
- **Use `asyncio.Queue` for producer/consumer patterns**

---

## Error Handling

### Exception Hierarchy

```python
# Define custom exceptions
class SlideshowError(Exception):
    """Base exception for slideshow operations."""
    pass

class GeminiAPIError(SlideshowError):
    """Gemini API call failed."""
    pass

class OutlineNotFoundError(SlideshowError):
    """Outline file not found."""
    pass

class ImageGenerationError(SlideshowError):
    """Image generation failed."""
    pass

# Use specific exceptions
async def load_outline(outline_id: str) -> Outline:
    try:
        data = await storage.load(outline_id)
    except FileNotFoundError as e:
        raise OutlineNotFoundError(f"Outline {outline_id} not found") from e

    try:
        return Outline.model_validate(data)
    except ValidationError as e:
        raise SlideshowError(f"Invalid outline data: {e}") from e
```

### Error Handling Patterns

```python
# Good: Let exceptions propagate up
async def api_handler():
    try:
        result = await service.do_work()
        return {"status": "success", "data": result}
    except OutlineNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except GeminiAPIError as e:
        logger.error("Gemini API error", exc_info=True)
        raise HTTPException(status_code=502, detail="External service error")
    except SlideshowError as e:
        logger.error("Slideshow error", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")

# Good: Retry with exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def call_gemini_api(prompt: str) -> bytes:
    # Will retry up to 3 times with exponential backoff
    return await gemini_client.generate_image(prompt)
```

---

## Logging

### Structured Logging with Structlog

```python
import structlog

# Configure in app/utils/logging.py
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if DEBUG else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Usage
logger.info("slide_generated", slide_id="abc123", prompt_length=len(prompt))
logger.error("gemini_api_failed", error=str(e), retry_count=3)
logger.warning("cache_miss", cache_key=cache_key)

# Add context
with structlog.contextvars.bound_contextvars(request_id=request_id):
    logger.info("processing_request")  # Automatically includes request_id
```

### Logging Best Practices

- **Use structured logging** (key-value pairs, not string formatting)
- **Log levels**: DEBUG (development), INFO (production events), WARNING (recoverable issues), ERROR (failures)
- **Include context**: request IDs, user IDs, resource IDs
- **Never log secrets**: API keys, tokens, passwords
- **Log at boundaries**: API entry/exit, external service calls, storage operations

---

## Dependencies

### Package Management with uv

```bash
# Initialize project
uv init

# Add dependencies
uv add fastapi uvicorn[standard] pydantic pydantic-settings
uv add httpx structlog tenacity pyyaml pillow
uv add google-genai  # Google Gemini SDK

# Add dev dependencies
uv add --dev pytest pytest-asyncio pytest-cov
uv add --dev ruff mypy
uv add --dev httpx-mock

# Sync environment
uv sync

# Run application
uv run python -m app.main

# Run tests
uv run pytest
```

### Core Dependencies (Latest Versions)

- **fastapi** (0.115+): Web framework
- **uvicorn[standard]** (0.32+): ASGI server
- **pydantic** (2.10+): Data validation
- **pydantic-settings** (2.6+): Settings management
- **httpx** (0.28+): Async HTTP client
- **structlog** (24.4+): Structured logging
- **tenacity** (9.0+): Retry logic
- **pyyaml** (6.0+): YAML parsing
- **pillow** (11.1+): Image processing
- **google-genai** (latest): Google Gemini SDK

### Development Dependencies

- **pytest** (8.3+): Testing framework
- **pytest-asyncio** (0.24+): Async test support
- **pytest-cov** (6.0+): Coverage reporting
- **ruff** (0.8+): Linter and formatter
- **mypy** (1.13+): Static type checker
- **httpx-mock** (0.16+): HTTP mocking

---

## Testing

### Test Structure

```python
# tests/conftest.py
import pytest
from pathlib import Path
from app.core.config import Settings

@pytest.fixture
def test_settings():
    return Settings(
        gemini_api_key="test-key",
        data_dir=Path("/tmp/test-data"),
    )

@pytest.fixture
async def mock_gemini_client():
    # Return mock client
    pass

# tests/unit/test_image_generator.py
import pytest
from app.services.image_generator import ImageGenerator

@pytest.mark.asyncio
async def test_generate_image_success(mock_gemini_client):
    generator = ImageGenerator(client=mock_gemini_client)

    result = await generator.generate("test prompt")

    assert result is not None
    assert len(result) > 0

@pytest.mark.asyncio
async def test_generate_image_api_error(mock_gemini_client):
    mock_gemini_client.generate.side_effect = Exception("API Error")
    generator = ImageGenerator(client=mock_gemini_client)

    with pytest.raises(GeminiAPIError):
        await generator.generate("test prompt")
```

### Testing Best Practices

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test API endpoints end-to-end
- **Use fixtures**: Share common test setup
- **Mock external services**: Don't call real APIs in tests
- **Test error cases**: Not just happy paths
- **Aim for 80%+ coverage**: Focus on critical paths

---

## Configuration

### Environment Variables

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-3-pro-image-preview"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # Storage Configuration
    data_dir: Path = Path("./data")

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # or "console"

    @property
    def outline_dir(self) -> Path:
        return self.data_dir / "outlines"

    @property
    def image_dir(self) -> Path:
        return self.data_dir / "images"

# Usage
settings = Settings()  # Loads from .env automatically
```

---

## Security

### API Key Management

- **Never commit `.env` files** - add to `.gitignore`
- **Use `.env.example`** - template without real secrets
- **Validate API keys on startup** - fail fast if missing

### Input Validation

- **Use Pydantic models** - automatic validation
- **Sanitize file paths** - prevent directory traversal
- **Limit file sizes** - prevent DoS attacks
- **Validate image formats** - only accept safe formats (PNG, JPEG)

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Performance

### Caching Strategies

```python
# Cache generated images by content hash
class ImageCache:
    def __init__(self, cache_dir: Path):
        self._cache_dir = cache_dir

    async def get(self, content_hash: str) -> bytes | None:
        cache_file = self._cache_dir / f"{content_hash}.png"
        if cache_file.exists():
            return cache_file.read_bytes()
        return None

    async def set(self, content_hash: str, data: bytes) -> None:
        cache_file = self._cache_dir / f"{content_hash}.png"
        cache_file.write_bytes(data)
```

### Rate Limiting

- **Limit concurrent API calls** - use `asyncio.Semaphore`
- **Implement request queuing** - prevent API quota exhaustion
- **Add retry logic** - with exponential backoff

---

## Common Pitfalls to Avoid

❌ **Don't** use blocking I/O in async functions
❌ **Don't** share mutable state between requests
❌ **Don't** catch exceptions without logging
❌ **Don't** use `print()` for logging
❌ **Don't** hardcode file paths or credentials
❌ **Don't** import from `api/` in `storage/` (wrong direction)
❌ **Don't** put business logic in API handlers
❌ **Don't** use global variables for request state

✅ **Do** use type hints everywhere
✅ **Do** validate input with Pydantic
✅ **Do** use structured logging
✅ **Do** write tests for critical paths
✅ **Do** handle errors explicitly
✅ **Do** follow the single responsibility principle
✅ **Do** use dependency injection
✅ **Do** keep functions small and focused

---

## Quick Reference

### Start Development Server

```bash
cd backend
source .venv/bin/activate  # or: . .venv/bin/activate
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/ --cov=app --cov-report=term-missing
```

### Lint and Format

```bash
uv run ruff format .
uv run ruff check . --fix
uv run mypy app/
```

### Project Commands

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Update dependencies
uv lock --upgrade

# Clean up
rm -rf .venv uv.lock
uv sync
```

---

**Last Updated**: 2026-02-01
**Python Version**: 3.12+
**Framework**: FastAPI 0.115+
