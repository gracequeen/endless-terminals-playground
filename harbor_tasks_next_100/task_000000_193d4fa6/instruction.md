Trying to cut a release from /home/user/webapp and `make release` is dying somewhere in the middle — it's supposed to build the frontend, backend, bundle them into dist/, tag, and write a manifest. Getting some error about a missing artifact but the individual targets seem fine when I run them standalone? Like `make frontend` works, `make backend` works, but the full release pipeline chokes.

Need it actually producing a clean release — dist/ with both bundles and a valid manifest.json that has the version and checksums.
