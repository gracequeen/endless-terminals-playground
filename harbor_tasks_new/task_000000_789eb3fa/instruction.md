I'm a technical writer who just joined a documentation team, and I need to set up a clean workspace for our docs repository. We have a shared documentation directory at /home/user/docs_workspace that needs to be organized with proper permissions for different document types.

Here's what I need:

1. Create the following directory structure under /home/user/docs_workspace:
   - /home/user/docs_workspace/public (for published docs anyone can read)
   - /home/user/docs_workspace/drafts (for work-in-progress, more restricted)
   - /home/user/docs_workspace/templates (read-only reference files)
   - /home/user/docs_workspace/archive (old versions, read-only)

2. Set up permissions as follows:
   - public: readable and writable by owner, readable by group and others (755 for directory)
   - drafts: readable and writable by owner only, no access for group or others (700)
   - templates: readable by everyone, writable only by owner (755 for directory)
   - archive: readable by owner and group, no access for others (750)

3. Create these starter files with the specified permissions:
   - /home/user/docs_workspace/public/index.md with content "# Documentation Home\n\nWelcome to the docs." (file permissions 644)
   - /home/user/docs_workspace/drafts/wip-feature.md with content "# Feature Draft\n\nWork in progress." (file permissions 600)
   - /home/user/docs_workspace/templates/article-template.md with content "# Title\n\n## Overview\n\n## Details\n\n## See Also" (file permissions 444)
   - /home/user/docs_workspace/archive/v1-notes.md with content "# Version 1 Notes\n\nLegacy documentation." (file permissions 440)

4. Create a manifest file at /home/user/docs_workspace/permissions_manifest.txt that documents the final state. The format must be exactly:

```
DIRECTORY_PERMISSIONS:
/home/user/docs_workspace/public:755
/home/user/docs_workspace/drafts:700
/home/user/docs_workspace/templates:755
/home/user/docs_workspace/archive:750

FILE_PERMISSIONS:
/home/user/docs_workspace/public/index.md:644
/home/user/docs_workspace/drafts/wip-feature.md:600
/home/user/docs_workspace/templates/article-template.md:444
/home/user/docs_workspace/archive/v1-notes.md:440
```

The manifest must have exactly this format with no extra whitespace, blank lines between sections (one blank line only as shown), and permissions in octal notation. The automated test will diff this file exactly.

5. Finally, create a script at /home/user/docs_workspace/verify_permissions.sh that when run outputs "PASS" if all permissions match the manifest, or "FAIL: <path>" for the first mismatched item. The script should be executable (755).
