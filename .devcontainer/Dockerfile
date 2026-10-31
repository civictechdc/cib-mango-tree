# Codespaces / Dev Container image for CIB Mango Tree.
# Scoped to container use only — does not change local or packaged app behavior.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Official uv binaries (same approach as Astral's Docker docs).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Shared libs for PyQt6 + QtWebEngine (aligned with .github/workflows/build_gui.yml).
# Drop the base image's Yarn apt source — its InRelease is often unsigned and
# breaks apt-get update in Codespaces builds.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/*yarn* \
    && apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libegl1 \
        libxkbcommon0 \
        libxkbcommon-x11-0 \
        libxcb1 \
        libxcb-cursor0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-render0 \
        libxcb-render-util0 \
        libxcb-shape0 \
        libxcb-shm0 \
        libxcb-xfixes0 \
        libxcb-xinerama0 \
        libxcb-randr0 \
        libfontconfig1 \
        libdbus-1-3 \
        libnss3 \
        libnspr4 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libxtst6 \
        libasound2 \
        libglib2.0-0 \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxi6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
