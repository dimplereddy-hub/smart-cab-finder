import asyncio
import logging
import threading
import time
from typing import Any

import glabflow
import msgspec

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def safe_api_call_async(coro_factory, *args, **kwargs):
    """
    Async safe wrapper for GitLab API calls with retry logic and 429 handling.
    Accepts a coroutine factory (callable that returns a coroutine).
    """
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return await coro_factory(*args, **kwargs)
        except glabflow.RateLimitError as e:
            raw_wait = getattr(e, "retry_after", None) or 5 * (attempt + 1)
            wait_time = min(raw_wait, 15)
            logger.warning(f"Rate limited (429). retry_after={raw_wait}s, capped to {wait_time}s.")
            if raw_wait > 15:
                raise Exception(f"GitLab API rate limit too high ({raw_wait}s). Try again later.") from e
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
                continue
            else:
                raise Exception("GitLab API Rate Limit Exceeded (429 Too Many Requests). Max retries reached.") from e
        except (glabflow.ServerError, glabflow.TransientError) as e:
            wait_time = 5 * (attempt + 1)
            logger.warning(f"Transient/Server Error: {e}. Waiting {wait_time}s...")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
                continue
            return []
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            logger.error(f"FAILED API CALL: {type(e).__name__} - {e}")
            return []
    return []


_JSON_DECODER = msgspec.json.Decoder()


def _decode_json(data) -> Any:
    """Decode JSON bytes or already-parsed data from glabflow."""
    if isinstance(data, (dict, list)):
        return data
    if isinstance(data, (bytes, bytearray)):
        try:
            return _JSON_DECODER.decode(data)
        except Exception:
            return []
    return data if data is not None else []


class GitLabClient:
    def __init__(self, base_url: str, private_token: str, ssl_verify: bool = True):
        self.base_url = base_url.rstrip("/")
        # glabflow expects the API base (with /api/v4)
        self.api_base = f"{self.base_url}/api/v4"
        self.private_token = private_token
        self.ssl_verify = ssl_verify
        self.error_msg = None
        self._gl: glabflow.Client | None = None

        # A background thread runs a dedicated event loop.
        # This keeps glabflow's async client isolated from Streamlit's loop.
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        logger.info(f"GitLabClient initialized. Background thread started: {self._thread.name}")

        self._sem: asyncio.Semaphore | None = None
        self._init_sem()

        # Shared response cache: path → (decoded_value, expiry_timestamp)
        # Keyed on the full URL path including query string.
        # Accessed only from the background event loop (single-threaded), so no lock needed.
        self._cache: dict[str, tuple[Any, float]] = {}
        self._cache_ttl: float = 300.0  # 5 minutes

        # Enter glabflow client context in the background loop
        self._init_gl_client()

    def _run_event_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _init_sem(self):
        async def create_sem():
            # 5 concurrent requests — conservative enough to avoid rate limits on shared instances
            return asyncio.Semaphore(5)

        fut = asyncio.run_coroutine_threadsafe(create_sem(), self._loop)
        self._sem = fut.result()

    def _run_sync(self, coro):
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return fut.result()

    def _init_gl_client(self):
        """Initialize and enter glabflow.Client as async context manager in background loop."""

        async def _enter():
            gl = glabflow.Client(
                base_url=self.api_base,
                token=self.private_token,
                ssl=self.ssl_verify,
                concurrency=25,
                timeout=30.0,
            )
            # CRITICAL: Disable global connector to prevent cross-loop Lock boundary errors in Streamlit
            await gl.__aenter__()
            return gl

        try:
            fut = asyncio.run_coroutine_threadsafe(_enter(), self._loop)
            self._gl = fut.result(timeout=30)
        except Exception as e:
            self.error_msg = str(e)
            logger.error(f"Failed to initialize glabflow client: {e}")
            self._gl = None

    @property
    def client(self):
        """Returns the glabflow Client instance (for compatibility)."""
        return self._gl

    async def _async_get(self, endpoint: str, params: dict | None = None) -> Any:
        """Single GET request via glabflow. Returns decoded JSON."""
        gl = self._gl
        if not gl:
            logger.error("GitLab client not initialized.")
            return []

        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if path.startswith("/api/v4"):
            path = path[len("/api/v4") :]

        # Robust handling of parameters via query string to avoid serialization issues
        if params:
            from urllib.parse import urlencode

            query = urlencode({k: v for k, v in params.items() if v is not None})
            connector = "&" if "?" in path else "?"
            path = f"{path}{connector}{query}"

        # Check response cache before hitting GitLab — shared across all users on this instance
        cached = self._cache.get(path)
        if cached is not None:
            value, expiry = cached
            if time.monotonic() < expiry:
                return value
            del self._cache[path]

        sem = self._sem
        if sem is None:
            return []

        try:
            async with sem:
                raw = await gl.get(path)
            result = _decode_json(raw)
            # Only cache non-empty responses — never cache [] or {} from failures
            if result:
                self._cache[path] = (result, time.monotonic() + self._cache_ttl)
            return result
        except glabflow.NotFoundError:
            return []
        except glabflow.RateLimitError as e:
            # Cap wait at 15s — never honour a server retry_after of 2000+ seconds
            # in a multi-user app; fail fast so the user sees an error immediately.
            raw_wait = getattr(e, "retry_after", None) or 5
            wait = min(raw_wait, 15)
            logger.warning(f"Rate limited on GET {path}. retry_after={raw_wait}s, capped to {wait}s.")
            self._cache.pop(path, None)
            if raw_wait > 15:
                logger.error(f"GitLab rate limit too high ({raw_wait}s). Returning empty for {path}.")
                return []
            await asyncio.sleep(wait)
            try:
                async with sem:
                    raw = await gl.get(path)
                return _decode_json(raw)
            except Exception as e:
                logger.error(f"Retry GET {path} failed: {e}")
                return []
        except Exception as e:
            logger.error(f"GET {path} failed: {type(e).__name__} - {e}")
            return []

    async def _async_request(self, method, endpoint, params=None):
        """Full HTTP request dispatcher (GET/POST/PUT/DELETE)."""
        gl = self._gl
        if not gl:
            return []

        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if path.startswith("/api/v4"):
            path = path[len("/api/v4") :]

        try:
            if self._sem is None:
                return []
            async with self._sem:
                if method.upper() == "GET":
                    if params:
                        from urllib.parse import urlencode

                        query = urlencode({k: v for k, v in params.items() if v is not None})
                        connector = "&" if "?" in path else "?"
                        path = f"{path}{connector}{query}"
                    raw = await gl.get(path)
                elif method.upper() == "POST":
                    raw = await gl.post(path, json=params or {})
                else:
                    raw = await gl.get(path)
            return _decode_json(raw)
        except glabflow.NotFoundError:
            return []
        except Exception as e:
            logger.error(f"{method} {path} failed: {type(e).__name__} - {e}")
            return []

    async def _async_get_paginated(self, endpoint, params=None, per_page=100, max_pages=10):
        """Paginated GET using glabflow's paginate() async generator."""
        gl = self._gl
        if not gl:
            return []

        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if path.startswith("/api/v4"):
            path = path[len("/api/v4") :]

        all_items: list = []
        p_params = {**(params or {}), "per_page": per_page}

        try:
            page_count = 0
            async for raw_page in gl.paginate(path, **p_params):
                page_count += 1
                page_data = _decode_json(raw_page)
                if isinstance(page_data, list):
                    all_items.extend(page_data)
                elif isinstance(page_data, dict):
                    all_items.append(page_data)
                if page_count >= max_pages:
                    break
        except Exception as e:
            logger.error(f"Paginated GET {path} failed: {type(e).__name__} - {e}")

        return all_items

    def _request(self, method, endpoint, params=None):
        return self._run_sync(self._async_request(method, endpoint, params))

    def _get(self, endpoint, params=None):
        return self._run_sync(self._async_get(endpoint, params=params))

    def _get_paginated(self, endpoint, params=None, per_page=100, max_pages=10):
        return self._run_sync(self._async_get_paginated(endpoint, params, per_page, max_pages))

    def close(self):
        """Shut down the background loop and thread gracefully."""
        try:
            # Exit glabflow client context
            if self._gl is not None:
                fut = asyncio.run_coroutine_threadsafe(self._gl.__aexit__(None, None, None), self._loop)
                try:
                    fut.result(timeout=5)
                except Exception:
                    pass
                self._gl = None

            # Stop the event loop
            if self._loop and self._loop.is_running():
                logger.info("Stopping GitLabClient background event loop...")
                self._loop.call_soon_threadsafe(self._loop.stop)

            # Wait for thread to finish
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2)
                logger.info(f"GitLabClient background thread joined: {self._thread.name}")
        except Exception as e:
            logger.error(f"Error during GitLabClient closure: {e}")
        finally:
            self._gl = None
            self._loop = None
            self._thread = None
            self._cache.clear()

    def __del__(self):
        self.close()
