"""Moa365 MCP proxy — PlayMCP in KC(카카오 클라우드) 배포용 경량 프록시.

Agentic Player 10 공모전 요건상 MCP Endpoint 는 PlayMCP in KC 발급 서버여야 한다.
이 프록시는 KC 에서 실행되며, MCP(Streamable HTTP JSON-RPC) 요청을
Moa365 백엔드(https://atm-ledger.onrender.com)로 그대로 전달만 한다.

- 시크릿 없음: Authorization 헤더는 사용자→카카오→프록시→백엔드로 그대로 통과(pass-through).
  실제 검증·데이터 접근은 전부 백엔드에서 수행된다.
- Stateless: 세션·저장소 없음 (PlayMCP 권장사항).
- OAuth 디스커버리(/.well-known/*)도 백엔드로 포워딩한다.
"""
from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, Request, Response

UPSTREAM = os.environ.get("UPSTREAM_BASE_URL", "https://atm-ledger.onrender.com").rstrip("/")

# 업스트림이 무료 티어 콜드스타트/AI 파싱으로 느릴 수 있어 여유 있게.
TIMEOUT = httpx.Timeout(90.0, connect=15.0)

# 요청 시 업스트림으로 전달할 헤더 (hop-by-hop 제외 화이트리스트)
FORWARD_REQUEST_HEADERS = {
    "authorization",
    "content-type",
    "accept",
    "mcp-session-id",
    "mcp-protocol-version",
    "last-event-id",
}
# 응답 시 클라이언트로 돌려줄 헤더
FORWARD_RESPONSE_HEADERS = {
    "content-type",
    "www-authenticate",
    "mcp-session-id",
    "cache-control",
}

app = FastAPI(title="Moa365 MCP Proxy", docs_url=None, redoc_url=None, openapi_url=None)

_client: httpx.AsyncClient | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=TIMEOUT)


@app.on_event("shutdown")
async def _shutdown() -> None:
    if _client:
        await _client.aclose()


async def _forward(request: Request, path: str) -> Response:
    assert _client is not None
    headers = {
        k: v for k, v in request.headers.items() if k.lower() in FORWARD_REQUEST_HEADERS
    }
    body = await request.body()
    try:
        upstream = await _client.request(
            request.method, f"{UPSTREAM}{path}", content=body or None, headers=headers
        )
    except httpx.HTTPError:
        return Response(
            content='{"jsonrpc":"2.0","id":null,"error":{"code":-32000,"message":"upstream unavailable"}}',
            status_code=502,
            media_type="application/json",
        )
    resp_headers = {
        k: v for k, v in upstream.headers.items() if k.lower() in FORWARD_RESPONSE_HEADERS
    }
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=resp_headers,
    )


@app.api_route("/mcp", methods=["POST", "GET", "DELETE"])
async def mcp(request: Request) -> Response:
    return await _forward(request, "/mcp")


@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata(request: Request) -> Response:
    return await _forward(request, "/.well-known/oauth-authorization-server")


@app.get("/.well-known/oauth-protected-resource")
async def resource_metadata(request: Request) -> Response:
    return await _forward(request, "/.well-known/oauth-protected-resource")


@app.get("/")
@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "moa365-mcp-proxy", "upstream": UPSTREAM}
