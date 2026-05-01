FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    git \
    sed \
    gawk \
    coreutils \
    dos2unix \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/releaser && chmod 0777 /home/user/releaser

WORKDIR /home/user/releaser

RUN git config --global user.email "test@example.com" && \
    git config --global user.name "Test User" && \
    git config --global init.defaultBranch main

RUN git init

RUN printf '2.4.7\r\n' > VERSION

RUN cat > CHANGELOG.md << 'CHANGELOGEOF'
# Changelog

All notable changes to this project will be documented in this file.

## [2.4.7] - 2024-01-10

- abc0001 Initial release preparation
- abc0002 Setup CI pipeline

## [2.4.6] - 2024-01-05

- def0001 Add authentication module
- def0002 Improve error handling

## [2.4.5] - 2024-01-01

- ghi0001 Project initialization
- ghi0002 Add README
CHANGELOGEOF

RUN cat > bump.sh << 'SCRIPTEOF'
#!/bin/bash
set -e
VERSION_FILE="VERSION"
CHANGELOG="CHANGELOG.md"

current=$(cat "$VERSION_FILE")
# Parse semver
major=$(echo "$current" | cut -d. -f1)
minor=$(echo "$current" | cut -d. -f2)
patch=$(echo "$current" | cut -d. -f3)

case "$1" in
    major) major=$((major + 1)); minor=0; patch=0 ;;
    minor) minor=$((minor + 1)); patch=0 ;;
    patch) patch=$((patch + 1)) ;;
    *) echo "Usage: $0 {major|minor|patch}"; exit 1 ;;
esac

# Bug: if patch increment fails (non-numeric due to \r), patch becomes empty
# Script has this "helpful" fallback added by previous maintainer:
if [ -z "$patch" ]; then
    minor=$((minor + 1))
    patch=0
fi

new_version="${major}.${minor}.${patch}"
echo "$new_version" > "$VERSION_FILE"

# Generate changelog block
date_str=$(date +%Y-%m-%d)
commits=$(git log --oneline --since="midnight" 2>/dev/null || echo "- No commits today")

# Bug 2: The heredoc indentation is wrong — there's a second git log call
# buried in a subshell that also runs, doubling the commits
{
    echo "## [$new_version] - $date_str"
    echo "$commits"
    echo "$(git log --oneline --since="midnight" 2>/dev/null)"
    echo ""
} > /tmp/new_changelog_block.txt

cat /tmp/new_changelog_block.txt "$CHANGELOG" > /tmp/changelog_merged.txt
mv /tmp/changelog_merged.txt "$CHANGELOG"

echo "Bumped to $new_version"
SCRIPTEOF

RUN chmod +x bump.sh

RUN echo "Initial setup file" > setup.txt && \
    git add setup.txt && \
    git commit -m "Initial commit" --date="2024-01-01 10:00:00"

RUN echo "More content" >> setup.txt && \
    git add setup.txt && \
    git commit -m "Second commit" --date="2024-01-02 10:00:00"

RUN git add VERSION CHANGELOG.md bump.sh && \
    git commit -m "Add release tooling" --date="2024-01-03 10:00:00"

RUN echo "feature1" > feature1.txt && \
    git add feature1.txt && \
    git commit -m "Add user export feature"

RUN echo "fix1" > fix1.txt && \
    git add fix1.txt && \
    git commit -m "Fix login timeout"

RUN echo "deps" > deps.txt && \
    git add deps.txt && \
    git commit -m "Update dependencies"

RUN chmod -R 0777 /home/user/releaser

WORKDIR /home/user
