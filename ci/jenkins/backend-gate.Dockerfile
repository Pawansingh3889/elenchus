# The image `make gate` runs inside.
#
# Deliberately close to backend/Dockerfile rather than a hand-rolled toolbox: same
# Python, same uv, brought in by the same COPY. A gate that installs dependencies
# with a different tool than the shipping image is testing a different build.
FROM docker.io/library/python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# make, because the pipeline calls `make gate` instead of restating its five steps.
# The Makefile is the single list of what CI runs, and .github/workflows/ci.yml
# already delegates to it for exactly that reason.
#
# git, because uv and the tooling under it shell out to it; without git the
# failures are obscure ones about revision resolution rather than a missing binary.
RUN apt-get update \
    && apt-get install -y --no-install-recommends make git \
    && rm -rf /var/lib/apt/lists/*
