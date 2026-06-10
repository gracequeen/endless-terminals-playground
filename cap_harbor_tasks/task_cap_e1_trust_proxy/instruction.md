All requests appear to originate from the same IP when running behind the Cloud Foundry load balancer. `express-rate-limit` reads the wrong address because Express doesn't trust the `X-Forwarded-For` header by default, so all clients are rate-limited as one.

Enable trust for the first upstream proxy in the Express app configuration so that `express-rate-limit` correctly reads the real client IP from `X-Forwarded-For`.

Run the tests to verify nothing is broken:

```bash
npm run test:unit
```
