# The image the frontend checks run inside.
#
# Node 22 to match .github/workflows/ci.yml and frontend/Dockerfile. pnpm is pinned
# to 11, the version ci.yml's pnpm/action-setup asks for: package.json carries no
# `packageManager` field, so nothing else in the repo pins it, and corepack would
# otherwise activate whatever is current on the day.
FROM docker.io/library/node:22-slim

RUN corepack enable && corepack prepare pnpm@11 --activate

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
