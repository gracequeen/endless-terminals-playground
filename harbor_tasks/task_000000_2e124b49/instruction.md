Trying to cut a release for the docs repo at /home/user/docs-site and `npm run release` just dies with some validation error about the changelog format. The script's supposed to bump the version in package.json based on conventional commits since the last tag, then prepend a new section to CHANGELOG.md. Worked fine last month.

I think someone might've hand-edited the changelog recently to fix a typo? Or maybe one of the recent commits has a malformed message, idk. The error isn't super helpful — just says "changelog validation failed" and exits 1.

Need the release script passing so I can get v0.8.0 out the door. Whatever's malformed, fix it, but keep the actual content intact — there's real release history in there I don't want to lose.
