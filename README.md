# Moa365 MCP Proxy

**Moa365(모아365)** — 대화하듯 한 줄로 기록하는 AI 가계부([moa365.com](https://moa365.com))의
MCP(Model Context Protocol) 프록시 서버입니다.

Agentic Player 10 공모전 / PlayMCP in KC(카카오 클라우드) 배포용으로,
MCP Streamable HTTP(JSON-RPC 2.0) 요청을 Moa365 백엔드로 전달합니다.

```
PlayMCP (카카오) ──► KC: moa365-mcp-proxy (이 저장소, 시크릿 없음)
                        └──► Moa365 backend /mcp (실제 도구 실행 · OAuth 2.0 + PKCE)
```

## 제공 도구 (tools)

| Tool | 설명 |
|------|------|
| `record_expense` | "스타벅스 6500원" 같은 자연어 한 줄을 AI가 파싱해 지출 기록 |
| `month_summary` | 월간 지출 합계·카테고리별 현황·예산 상태 요약 |
| `set_budget` | 월 예산 등록·변경 (0 = 해제) |
| `get_budget` | 이번 달 예산·지출·잔액 조회 (미설정 시 안내) |
| `list_recent_expenses` | 최근 지출 내역 조회 |

## 구조

- **Stateless** — 세션 없음 (PlayMCP 권장)
- **시크릿 없음** — `Authorization` 헤더는 그대로 통과(pass-through)하며,
  토큰 검증·사용자 격리·데이터 접근은 전부 Moa365 백엔드가 수행
- 사용자 인증은 표준 OAuth 2.0 Authorization Code + PKCE(S256)
  (`/.well-known/oauth-authorization-server` 디스커버리 포워딩)

## 실행

```bash
docker build --platform linux/amd64 -t moa365-mcp-proxy .
docker run -p 8080:8080 moa365-mcp-proxy
# → POST http://localhost:8080/mcp
```

환경변수 `UPSTREAM_BASE_URL` (기본: `https://atm-ledger.onrender.com`),
`PORT` (기본: `8080`).
