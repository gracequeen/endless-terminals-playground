**Bug:** The `WEBAGENTS_BACKEND` BTP destination is configured with `OAuth2UserTokenExchange` but the IAS Application-to-Application trust between this service and the backend has not yet been established. As a result, every `chat.filesync` event delivery fails with `'Failed to load destination'` and the backend never receives the events.

As a temporary fix, the event proxy (`src/lib/event-proxy.js`) should fall back to a direct HTTP call using `webagentsUrl` when `executeHttpRequest` throws a destination-not-found error, so events are not dropped while the trust setup is pending.

Add a test covering the fallback behavior. Verify with:

```bash
npm run test:unit
```
