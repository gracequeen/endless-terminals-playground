**Cleanup:** After a framework migration from Fastify to SAP CAP, several files are now dead code:

- `src/lib/errors.js` and `src/lib/errors.test.js` — Fastify-era error helpers, no longer used (CAP uses `req.error()`)
- `src/migrations/` directory — empty since CAP migration replaced SQL migrations with `db/schema.cds`

Additionally, `package.json` has stale references:
- The test glob `src/config/**/*.test.js` no longer exists
- `chai` and `@eslint/js` are listed as devDependencies but are unused

Remove the dead files and clean up the stale references in `package.json`. Run the tests to confirm they still pass:

```bash
npm run test:unit
```
