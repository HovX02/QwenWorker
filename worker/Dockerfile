ARG CUDA_VERSION=12.6.3
ARG UBUNTU_VERSION=24.04
FROM nvidia/cuda:${CUDA_VERSION}-cudnn-devel-ubuntu${UBUNTU_VERSION} AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential git cmake ca-certificates curl gnupg && \
 mkdir -p /etc/apt/keyrings && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key -o /tmp/nodesource-repo.gpg.key && \
 gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg /tmp/nodesource-repo.gpg.key && rm /tmp/nodesource-repo.gpg.key && \
 echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
 apt-get update && apt-get install -y --no-install-recommends nodejs && npm install -g pnpm@10.15.1 && rm -rf /var/lib/apt/lists/*
WORKDIR /sd.cpp
RUN git clone --recursive https://github.com/leejet/stable-diffusion.cpp.git .
RUN cmake -S . -B build -DSD_CUDA=ON
RUN cmake --build build --config Release -j2
FROM nvidia/cuda:${CUDA_VERSION}-cudnn-runtime-ubuntu${UBUNTU_VERSION} AS runtime
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 HF_HOME=/tmp/hf-home HF_HUB_DISABLE_TELEMETRY=1 MODEL_DIR=/tmp/qwen-models
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv libgomp1 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /sd.cpp/build/bin /sd.cpp/bin
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir --upgrade pip && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
COPY handler.py .
ENV PATH="/opt/venv/bin:/sd.cpp/bin:${PATH}"
CMD ["python3", "-u", "/app/handler.py"]
