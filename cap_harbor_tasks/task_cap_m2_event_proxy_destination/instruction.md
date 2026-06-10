**Feature:** The event proxy (`src/lib/event-proxy.js`) currently only has a local `fetch`-based delivery path. In production, when a `destination` binding is present in `VCAP_SERVICES`, it should use `@sap-cloud-sdk/http-client.executeHttpRequest` with `destinationName: 'WEBAGENTS_BACKEND'` and forward the inbound user JWT so that the BTP Destination service can perform OAuth2 user-token-exchange and mint a fresh backend-audience token before the call.

The local fetch path must remain intact for development environments where no destination binding is present.

Extend `src/lib/event-proxy.js` with the production BTP path and add tests for both paths. Verify with:

```bash
npm run test:unit
```
