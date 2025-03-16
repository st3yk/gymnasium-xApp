ARG PARENT_IMAGE
FROM python_xapp_runner:i-release

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    python3-setuptools \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch (CPU version, change if using GPU)
RUN pip install torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu

# Install Stable-Baselines3
RUN pip install stable-baselines3[extra]==2.4.1

# Optional: Verify installation
RUN python -c "import stable_baselines3; import torch; print('Installation successful!')"
