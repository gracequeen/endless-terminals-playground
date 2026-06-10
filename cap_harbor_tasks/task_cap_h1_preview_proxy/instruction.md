**Security:** Raw partner preview URLs (`*.vusercontent.net` for v0, `*.lovable.dev` for Lovable) are currently returned directly to the browser. Anyone who learns the URL can bypass SAP authentication and view generated apps.

The gateway needs a reverse proxy that streams partner preview content through itself so the raw partner origin never reaches the browser. Requirements:

1. Every request must be gated through authentication
2. Occurrences of the raw partner origin string in HTML/CSS/JS response bodies must be rewritten to the proxy base path
3. A `Content-Security-Policy` header must be attached to every proxied response

Implement the proxy in `src/lib/preview-proxy.js` and register it in `srv/server.js` under `/api/preview/:partner/:solutionId/:assetName/*`. Add unit tests. Verify with:

```bash
npm run test:unit
```
