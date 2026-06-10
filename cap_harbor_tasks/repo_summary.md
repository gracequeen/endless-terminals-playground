# app-generation-gateway — Repo Summary

## Purpose

`app-generation-gateway` (AGG) is a Node.js/SAP CAP backend service that acts as a broker between SAP's internal tooling (Process Builder / Design Studio / webagents-backend) and external AI-powered app generation platforms (v0 by Vercel, Lovable). It accepts SAP-internal identifiers, delegates app creation and chat to partner SDKs, syncs generated files back into SAP's storage, and forwards streaming events to the webagents-backend.


## Technology Stack

- **Runtime**: Node.js ≥ 20, ESM (`"type": "module"`)
- **Framework**: SAP CAP (`@sap/cds` v9) — replaces an earlier Fastify 5 implementation
- **Database**: SAP HANA (production), SQLite in-memory (test), SQLite file (dev)
- **Auth**: SAP IAS (production), mocked (dev/test)
- **Linter/formatter**: Biome
- **Test runner**: Node.js built-in `node:test` with `tsx` for TypeScript support
- **Coverage**: `c8`
- **Deployment**: SAP BTP Cloud Foundry via MTA (`mta.yaml`)


## Repository Layout

```
app-generation-gateway/
├── db/
│   └── schema.cds              # CDS data model (ProjectMappings, ProjectFiles)
├── srv/
│   ├── server.js               # CAP bootstrap — Express middleware, preview proxy route
│   ├── v0-service.cds/.js      # V0Service: createApp, sendMessage, getFiles, getPreview, getStatus, deleteAppsForSolution
│   ├── lovable-service.cds/.js # LovableService: createApp, sendMessage, getFiles, getPreview
│   └── health-service.cds/.js  # GET /health — unauthenticated
├── src/
│   ├── connectors/
│   │   ├── v0/                 # v0-sdk wrapper (client + agent + worker)
│   │   └── lovable/            # Lovable SDK wrapper (client + agent)
│   └── lib/
│       ├── audit.js            # SEC-215 security event emission + authAuditMiddleware
│       ├── backend-files.js    # Fetch files from webagents-backend for PRD seeding
│       ├── event-proxy.js      # Resilient event forwarder → webagents-backend
│       ├── partner-url.ts      # SSRF allowlist for partner preview URLs
│       ├── partner-url.js      # CJS shim re-exporting partner-url.ts
│       ├── preview-proxy.js    # Reverse proxy: streams partner previews, rewrites URLs, sets CSP
│       ├── preview-url.js      # Builds AGG proxy URL from (partner, solutionId, assetPath)
│       ├── project-files.js    # Reads/writes ProjectFiles via CAP attachments plugin
│       └── service-token.js    # IAS X.509 mTLS client_credentials token provider
├── test/                       # Integration tests (require running CAP server + SQLite)
├── docs/                       # Architecture, runbooks, compliance plans
└── package.json                # Scripts: test:unit, test:integration, lint, format
```


## Data Model

Two CDS entities in namespace `agg`:

**`ProjectMappings`** — core mapping table. Unique constraint on `(partnerType, solutionId, assetPath)`.

| Field | Type | Notes |
|---|---|---|
| `solutionId` | String | SAP solution identifier |
| `assetPath` | String | Asset dir within solution (e.g. `assets/my-app`) |
| `partnerType` | `'v0' \| 'lovable'` | |
| `partnerProjectId` | String | Partner-assigned project ID |
| `partnerChatId` | String | Partner-assigned chat/conversation ID |
| `partnerPreviewUrl` | String | Live preview URL — server-side only, never returned to clients |
| `tenant` | String | Populated at insert from `cds.context.tenant` |
| `status` | `active \| inactive \| error` | |
| `creationStatus` | `creating \| ready \| failed` | Drives idempotent createApp |

**`ProjectFiles`** — generated file storage via `@cap-js/attachments`. Linked by `(solutionId, assetPath)`.


## API Surface

All endpoints require authentication (`@requires: 'authenticated-user'`) except `/health`.

**V0Service** — `@path: '/api/v0'`
- `POST createApp` — creates v0 project + chat, returns `(solutionId, assetPath, previewUrl, creationStatus)`
- `POST sendMessage` — sends follow-up prompt, returns content + thoughts
- `GET getFiles` / `getFilesWithContent` — list/return synced files
- `GET getPreview` — returns proxy preview URL
- `GET getStatus` — polls `creationStatus` (creating / ready / failed)
- `POST deleteAppsForSolution` — removes all v0 projects for a solution

**LovableService** — `@path: '/api/lovable'`
- `POST createApp`, `POST sendMessage`, `GET getFiles`, `GET getPreview`

**Preview proxy** — `GET /api/preview/:partner/:solutionId/:assetName/*`
- Streams partner content through AGG; rewrites partner origin URLs in bodies; attaches CSP header; auth-gated

**HealthService** — `GET /health` (unauthenticated)


## Key Modules

**`srv/server.js`** — CAP `bootstrap` hook. Registers: trust-proxy setting, `authAuditMiddleware`, Helmet, CORS, rate limiters (100 req/min general; 2000 req/min preview with per-user keying). On `served`, mounts the preview proxy route with CAP middleware chain.

**`src/lib/event-proxy.js`** — Forwards partner streaming events (`chat.message`, `chat.thinking`, `chat.preview`, `chat.filesync`, etc.) to `webagents-backend /api/v1/events/ingest`. Retry: 3 attempts, exponential backoff (1s/2s/4s). In-memory buffer (500 events). Dead-letter audit log after exhaustion. Production path uses `@sap-cloud-sdk/http-client` via BTP Destination service with OAuth2 user-token-exchange; dev path uses direct fetch to `webagentsUrl`.

**`src/lib/preview-proxy.js`** — Reverse proxy that streams partner preview content. Two defenses: (1) body rewrite replaces raw partner origin string with AGG proxy base path; (2) strict CSP on every response. `resolveTarget` callback enforces auth, tenant match, and ownership before any fetch.

**`src/lib/partner-url.ts`** — SSRF allowlist. Validates that stored `partnerPreviewUrl` is HTTPS, default port, no credentials, and matches per-partner host patterns (`*.vusercontent.net` / `*.v0.app` / `*.v0.dev` for v0; `*.lovable.dev` / `*.lovable.app` / `*.lovableproject.com` for Lovable).

**`src/lib/service-token.js`** — Mints IAS OAuth2 `client_credentials` tokens via mTLS (X.509) for service-to-service calls. 30s cache skew. Returns mock token in non-production when no IAS binding is present.

**`src/lib/audit.js`** — Emits `SecurityEvent` to SAP Audit Log Service (SEC-215). Fire-and-forget, runs in detached `cds.tx`. `authAuditMiddleware` captures 401s; service handlers emit 403/404 denials with richer context.


## Test Structure

- **Unit tests**: `src/lib/**/*.test.{js,ts}`, `src/connectors/**/*.test.{js,ts}`, `srv/**/*.test.{js,ts}` — run via `npm run test:unit`. Use Node.js `node:test` with `--experimental-test-module-mocks`. No external dependencies required.
- **Integration tests**: `test/**/*.test.{js,ts}` — run via `npm run test:integration`. Spin up a full CAP server with SQLite in-memory DB. Require `CDS_ENV=test`.


## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `V0_API_KEY` | — | v0 partner SDK authentication |
| `LOVABLE_API_KEY` | — | Lovable partner SDK authentication |
| `CORS_ORIGIN` | `false` | Allowed CORS origin |
| `RATE_LIMIT_MAX` | `100` | General rate limit (req/min) |
| `PREVIEW_RATE_LIMIT_MAX` | `2000` | Preview proxy rate limit (req/min) |
| `PREVIEW_PROXY_BASE_URL` | `/api/v1/preview` | Override when gateway is on a different origin |
| `PREVIEW_MAX_REQUEST_BODY_BYTES` | `2097152` (2MB) | Max proxied request body size |
| `VCAP_SERVICES` | — | CF-injected; provides HANA, audit-log, IAS, destination bindings |
| `SERVICE_TOKEN_CACHE_SKEW_MS` | `30000` | IAS token cache expiry buffer |


## Security Design

- **SSRF prevention**: `partnerPreviewUrl` validated against per-partner host allowlist at write time and again at proxy time (defence in depth).
- **Preview isolation**: `Content-Security-Policy` on all proxied responses; `frame-ancestors 'self'`; `sandbox allow-scripts allow-forms allow-popups` (without `allow-same-origin` to prevent sandbox escape).
- **Tenant isolation**: Every `ProjectMappings` lookup is scoped by `tenant` in the query; post-query re-check on returned rows.
- **Ownership**: `createApp`/`sendMessage`/preview access checks `createdBy === user.id`.
- **Audit**: All 401s (via middleware) and 403/404 denials (via handlers) emit `SecurityEvent` to SAP Audit Log.
- **Rate limiting**: Two-tier — general API and preview-specific, with per-user keying in production.
