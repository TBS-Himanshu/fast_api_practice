from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid
from datetime import datetime, timezone
from .config import log_event
import traceback
import json

SKIP_LOGGING_PATHS = ["/docs", "/openapi.json", "/health", "/logs"]
SENSITIVE_KEYS = {"password", "authorization", "token", "access_token", "refresh_token", "secret", "cookie", "set-cookie"}


def redact(data):
    if isinstance(data, dict):
        return {
            k: ("***REDACTED***" if k.lower() in SENSITIVE_KEYS else redact(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [redact(item) for item in data]
    return data


def safe_body_for_log(raw_bytes: bytes) -> str:
    """Try to parse as JSON and redact; fall back to raw text if not JSON."""
    text = raw_bytes.decode("utf-8", errors="ignore")
    try:
        parsed = json.loads(text)
        return json.dumps(redact(parsed))
    except (json.JSONDecodeError, TypeError):
        return text  # not JSON — form data, plain text, etc. Can't structurally redact


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_LOGGING_PATHS:
            return await call_next(request)

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # capture request body, then "replay" it so the route can still read it
        body_bytes = await request.body()

        async def fake_receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = fake_receive

        log_event({
            "uuid": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "request",
            "method": request.method,
            "path": request.url.path,
            "headers": redact(dict(request.headers)),
            "body": safe_body_for_log(body_bytes),
        })

        try:
            response = await call_next(request)
        except Exception as e:
            log_event({
                "uuid": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            return Response(
                content=json.dumps({"message": "Something went wrong", "uuid": request_id, 'error': str(e)}),
                status_code=500,
                media_type="application/json",
            )

        # drain the response body stream
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        log_event({
            "uuid": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "response",
            "status_code": response.status_code,
            "headers": redact(dict(response.headers)),
            "body": safe_body_for_log(response_body),
        })

        # rebuild a fresh response with the same bytes, since original stream is now empty
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )