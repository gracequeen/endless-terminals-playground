FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git \
    python3.11 \
    python3-pip \
    jq \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

WORKDIR /home/user/releaser

RUN git init && \
    git config user.email "test@example.com" && \
    git config user.name "Test User"

RUN cat > package.json << 'PKGEOF'
{
  "name": "releaser",
  "version": "1.2.3",
  "description": "Release tooling"
}
PKGEOF

RUN cat > CHANGELOG.md << 'CLEOF'
# Changelog

## [1.2.3] - 2024-01-15

### Fixed
- Fixed memory leak in data processor

### Added
- Initial AWS billing integration

## [1.2.2] - 2024-01-10

### Fixed
- Minor bug fixes
CLEOF

RUN cat > bump.py << 'BUMPEOF'
#!/usr/bin/env python3
"""
Version bump calculator based on conventional commits.
"""

import subprocess
import sys
import re
import json


def get_current_version():
    """Read current version from package.json."""
    with open('package.json', 'r') as f:
        data = json.load(f)
    return data.get('version', '0.0.0')


def get_commits_since_tag(tag):
    """Get all commits since the given tag."""
    # BUG #1: Using three dots instead of two dots
    cmd = f"git log v{tag}...HEAD --pretty=format:%s"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    commits = result.stdout.strip().split('\n')
    return [c for c in commits if c]


def parse_commit_type(message):
    """Parse the type from a conventional commit message."""
    # BUG #2: Missing optional scope pattern (\([^)]+\))?
    # This regex won't match commits like "feat(api): something"
    pattern = r'^(feat|fix|docs)\s*:'
    match = re.match(pattern, message)
    if match:
        return match.group(1)
    return 'other'


def determine_bump_type(commits):
    """Determine the bump type based on commits."""
    bump_types = []

    for commit in commits:
        commit_type = parse_commit_type(commit)
        if commit_type == 'feat':
            bump_types.append('minor')
        elif commit_type == 'fix':
            bump_types.append('patch')
        # docs and other don't trigger version bumps

    if not bump_types:
        return None

    # BUG #3: Using string max - "patch" > "minor" > "major" alphabetically
    # This is wrong! Should be major > minor > patch in precedence
    bump = max(bump_types)
    return bump


def bump_version(version, bump_type):
    """Bump the version according to semver."""
    parts = version.split('.')
    major = int(parts[0])
    minor = int(parts[1])
    patch = int(parts[2])

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1

    return f"{major}.{minor}.{patch}"


def generate_changelog_entries(commits):
    """Generate changelog entries grouped by type."""
    features = []
    fixes = []
    docs = []
    other = []

    for commit in commits:
        commit_type = parse_commit_type(commit)
        # Remove the type prefix for cleaner changelog
        clean_msg = re.sub(r'^(feat|fix|docs)\s*:\s*', '', commit)

        if commit_type == 'feat':
            features.append(clean_msg)
        elif commit_type == 'fix':
            fixes.append(clean_msg)
        elif commit_type == 'docs':
            docs.append(clean_msg)
        else:
            other.append(commit)

    return {
        'features': features,
        'fixes': fixes,
        'docs': docs,
        'other': other
    }


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--changelog':
        # Changelog mode
        current = get_current_version()
        commits = get_commits_since_tag(current)
        entries = generate_changelog_entries(commits)

        print("### Added")
        for f in entries['features']:
            print(f"- {f}")
        print("\n### Fixed")
        for f in entries['fixes']:
            print(f"- {f}")
        if entries['docs']:
            print("\n### Documentation")
            for d in entries['docs']:
                print(f"- {d}")
        if entries['other']:
            print("\n### Other Changes")
            for o in entries['other']:
                print(f"- {o}")
    else:
        # Version calculation mode
        current = get_current_version()
        commits = get_commits_since_tag(current)
        bump_type = determine_bump_type(commits)

        if bump_type:
            new_version = bump_version(current, bump_type)
            print(new_version)
        else:
            print(current)


if __name__ == '__main__':
    main()
BUMPEOF

RUN chmod +x bump.py

RUN cat > release.sh << 'RELEOF'
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Calculating new version..."
NEW_VERSION=$(python3 bump.py)
CURRENT_VERSION=$(jq -r '.version' package.json)

if [ "$NEW_VERSION" == "$CURRENT_VERSION" ]; then
    echo "No version bump needed."
    exit 0
fi

echo "Bumping version from $CURRENT_VERSION to $NEW_VERSION"

# Update package.json
jq ".version = \"$NEW_VERSION\"" package.json > package.json.tmp && mv package.json.tmp package.json

# Generate changelog entry
echo "Generating changelog..."
CHANGELOG_ENTRY=$(python3 bump.py --changelog)
DATE=$(date +%Y-%m-%d)

# Create new changelog content
{
    echo "# Changelog"
    echo ""
    echo "## [$NEW_VERSION] - $DATE"
    echo ""
    echo "$CHANGELOG_ENTRY"
    echo ""
    # Append old changelog (skip the first "# Changelog" line)
    tail -n +3 CHANGELOG.md
} > CHANGELOG.md.tmp && mv CHANGELOG.md.tmp CHANGELOG.md

# Git operations
git add package.json CHANGELOG.md
git commit -m "chore(release): $NEW_VERSION"
git tag "v$NEW_VERSION"

echo "Released version $NEW_VERSION"
echo "$NEW_VERSION"
RELEOF

RUN chmod +x release.sh

RUN git add package.json CHANGELOG.md bump.py release.sh && \
    git commit -m "Initial commit with release tooling"

RUN git tag v1.2.3

RUN echo "placeholder" > .placeholder && \
    git add .placeholder && \
    git commit -m "fix: resolve null pointer in payment processor"

RUN echo "placeholder2" > .placeholder2 && \
    git add .placeholder2 && \
    git commit -m "feat: add multi-currency support for AWS billing"

RUN echo "placeholder3" > .placeholder3 && \
    git add .placeholder3 && \
    git commit -m "fix: correct rounding error in cost allocation"

RUN echo "placeholder4" > .placeholder4 && \
    git add .placeholder4 && \
    git commit -m "docs: update README with new env vars"

RUN echo "placeholder5" > .placeholder5 && \
    git add .placeholder5 && \
    git commit -m "feat(api): expose historical spend endpoint"

RUN chown -R 1000:1000 /home/user && chmod -R 0777 /home/user

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
