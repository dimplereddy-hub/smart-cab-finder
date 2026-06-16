from unittest.mock import AsyncMock, patch

import glabflow
import pytest

from gitlab_compliance_checker.infrastructure.gitlab.client import GitLabClient, safe_api_call_async


@pytest.mark.asyncio
async def test_safe_api_call_success():
    """Returns result on success."""

    async def mock_func(x):
        return x * 2

    assert await safe_api_call_async(mock_func, 5) == 10


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_safe_api_call_429_retry(mock_sleep):
    """Retries on 429 with backoff."""
    mock_func = AsyncMock()
    err_429 = glabflow.RateLimitError("Rate limited", status_code=429, url="http", retry_after=5)
    mock_func.side_effect = [err_429, "success"]

    result = await safe_api_call_async(mock_func)
    assert result == "success"
    assert mock_sleep.call_count == 1
    mock_sleep.assert_called_with(5)


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_safe_api_call_429_max_retries(mock_sleep):
    """Raises exception after max retries for 429."""
    err_429 = glabflow.RateLimitError("Rate limited", status_code=429, url="http", retry_after=5)
    mock_func = AsyncMock(side_effect=err_429)
    with pytest.raises(Exception, match="Max retries reached"):
        await safe_api_call_async(mock_func)


def test_gitlab_client_init():
    client = GitLabClient("https://gitlab.com/", "token")
    assert client.base_url == "https://gitlab.com"
    assert client.api_base == "https://gitlab.com/api/v4"
