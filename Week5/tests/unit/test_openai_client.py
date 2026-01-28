"""OpenAI 客户端测试。

测试 OpenAI API 集成的核心功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from postgres_mcp.ai.openai_client import AIServiceUnavailableError, OpenAIClient


@pytest.fixture
def openai_config():
    """OpenAI 配置 fixture。"""
    return {
        "api_key": "test-api-key",
        "model": "gpt-4o-mini-2024-07-18",
        "temperature": 0.0,
        "max_tokens": 2000,
        "timeout": 10.0,
    }


@pytest.fixture
def openai_client(openai_config):
    """OpenAI 客户端 fixture。"""
    return OpenAIClient(**openai_config)


@pytest.mark.asyncio
async def test_openai_client_generate_success(openai_client):
    """Test successful SQL generation."""
    # Mock OpenAI API response
    mock_response = ChatCompletion(
        id="test-id",
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        created=1234567890,
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=(
                        '{"sql": "SELECT * FROM users LIMIT 1000;", '
                        '"explanation": "Query all users", '
                        '"assumptions": []}'
                    ),
                ),
                finish_reason="stop",
            )
        ],
    )

    with patch.object(
        openai_client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response

        result = await openai_client.generate(
            system_prompt="You are a SQL expert.",
            user_prompt="Generate SQL for: show all users",
        )

        assert result.sql == "SELECT * FROM users LIMIT 1000;"
        assert result.explanation == "Query all users"
        assert isinstance(result.assumptions, list)
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_openai_client_timeout(openai_client):
    """Test API timeout handling."""
    with patch.object(
        openai_client._client.chat.completions,
        "create",
        new_callable=AsyncMock,
        side_effect=TimeoutError("Request timeout"),
    ):
        with pytest.raises(AIServiceUnavailableError, match="OpenAI API timeout"):
            await openai_client.generate(
                system_prompt="Test", user_prompt="Test query"
            )


@pytest.mark.asyncio
async def test_openai_client_rate_limit(openai_client):
    """Test rate limit handling."""
    from openai import RateLimitError

    mock_error = RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429),
        body=None,
    )

    with patch.object(
        openai_client._client.chat.completions,
        "create",
        new_callable=AsyncMock,
        side_effect=mock_error,
    ):
        with pytest.raises(AIServiceUnavailableError, match="rate limit"):
            await openai_client.generate(
                system_prompt="Test", user_prompt="Test query"
            )


@pytest.mark.asyncio
async def test_openai_client_retry_logic(openai_client):
    """测试重试逻辑。"""
    mock_response = ChatCompletion(
        id="test-id",
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        created=1234567890,
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content='{"sql": "SELECT 1;", "explanation": "Test", "assumptions": []}',
                ),
                finish_reason="stop",
            )
        ],
    )

    # 第一次失败，第二次成功
    with patch.object(
        openai_client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.side_effect = [
            TimeoutError("First attempt timeout"),
            mock_response,
        ]

        result = await openai_client.generate(
            system_prompt="Test", user_prompt="Test query", max_retries=2
        )

        assert result.sql == "SELECT 1;"
        assert mock_create.call_count == 2


@pytest.mark.asyncio
async def test_openai_client_invalid_json_response(openai_client):
    """Test invalid JSON response handling."""
    mock_response = ChatCompletion(
        id="test-id",
        model="gpt-4o-mini-2024-07-18",
        object="chat.completion",
        created=1234567890,
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content="This is not valid JSON",
                ),
                finish_reason="stop",
            )
        ],
    )

    with patch.object(
        openai_client._client.chat.completions, "create", new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response

        with pytest.raises(AIServiceUnavailableError, match="Failed to parse"):
            await openai_client.generate(
                system_prompt="Test", user_prompt="Test query"
            )
