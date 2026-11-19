# The harness sandbox: headless Blender for agent-written code, run with no network, a read-only
# root, no capabilities and one writable folder (the run). Build once:
#
#     docker build -t agentic3d-blender:5.2.3 sandbox
#
# The rig's harness-sandbox setup starts one container per run (rig/setups/sandbox.py).
FROM debian:bookworm-slim

ARG BLENDER_VERSION=5.2.3
ARG BLENDER_SHA256=78486c018b4443efe5e75ab54c290ed8c15abafd249b862c2c9ce2530a918eec

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl xz-utils \
        libx11-6 libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 \
        libgl1 libegl1 libglu1-mesa libgomp1 libxext6 libxrandr2 libxinerama1 libxcursor1 \
        libwayland-client0 libwayland-cursor0 libwayland-egl1 libdbus-1-3 libfontconfig1 \
    && curl -fsSL -o /tmp/blender.tar.xz \
        "https://download.blender.org/release/Blender5.2/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && echo "${BLENDER_SHA256}  /tmp/blender.tar.xz" | sha256sum -c - \
    && mkdir /opt/blender \
    && tar -xJf /tmp/blender.tar.xz -C /opt/blender --strip-components=1 \
    && rm /tmp/blender.tar.xz \
    && apt-get purge -y curl xz-utils && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Unprivileged user; the rig also passes --user so files in the run folder aren't root-owned.
RUN useradd --uid 1000 --create-home agent
USER agent
WORKDIR /work
ENTRYPOINT ["/opt/blender/blender"]
