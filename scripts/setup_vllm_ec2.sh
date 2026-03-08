#!/bin/bash
# ============================================
# vLLM EC2 Setup Script for Qwen Models
# Budget: ~$50/month
# ============================================

set -e

echo "=== vLLM EC2 Setup for Qwen Models ==="

# ============================================
# RECOMMENDED EC2 CONFIGURATION ($50/month budget)
# ============================================
# Instance Type: t3.large (2 vCPU, 8GB RAM) - CPU only
# - Monthly cost: ~$30.24 (on-demand) or ~$9.07 (spot - 70% savings)
#
# For GPU: g4dn.xlarge (1x NVIDIA T4, 16GB VRAM)
# - Monthly cost: ~$75 (on-demand) or ~$25 (spot)
#
# Storage: 50GB gp3 EBS (~$5/month)
# - Needed for model weights

# ============================================
# INSTANCE SETUP
# ============================================

# Update system
echo "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11+ if not present
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    sudo apt-get install -y python3.11 python3.11-venv python3-pip
fi

# Install CUDA drivers (for GPU instances)
# For GPU instances, use the official NVIDIA CUDA installer
# For CPU-only: skip GPU-related steps

# Install PyTorch
echo "Installing PyTorch..."
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install vLLM
echo "Installing vLLM..."
pip3 install vllm>=0.4.0

# Install transformers for Qwen
echo "Installing transformers..."
pip3 install transformers>=4.37.0

# ============================================
# MODEL CONFIGURATIONS
# ============================================
#
# OPTION 1: CPU-only (t3.large) - $35/month
# - Text embeddings: intfloat/e5-small-v2 (384 dims)
# - Image embeddings: openai/clip-vit-large-patch14-336 (768 dims)
# Note: CPU-only may be slow for embeddings
#
# OPTION 2: GPU (g4dn.xlarge) - $75/month (or $25 spot)
# - Vision: Qwen/Qwen2-VL-2B-Instruct
# - Text/Image: Same as above OR use Qwen2-VL for both
#
# IMPORTANT: vLLM serves ONE model at a time
# You need to run separate vLLM instances for different model types

# ============================================
# START SCRIPTS
# ============================================

# Create startup script for text embeddings (CPU)
cat > ~/start_vllm_text.sh << 'EOF'
#!/bin/bash
# Start vLLM with text embeddings (e5-small-v2)
echo "Starting vLLM server with text embeddings..."
python3 -m vllm.entrypoints.openai.api_server \
    --model intfloat/e5-small-v2 \
    --host 0.0.0.0 \
    --port 8001 \
    --dtype half \
    --max-model-len 512
EOF

# Create startup script for image embeddings (CLIP)
cat > ~/start_vllm_image.sh << 'EOF'
#!/bin/bash
# Start vLLM with CLIP image embeddings
echo "Starting vLLM server with image embeddings (CLIP)..."
python3 -m vllm.entrypoints.openai.api_server \
    --model openai/clip-vit-large-patch14-336 \
    --host 0.0.0.0 \
    --port 8002 \
    --dtype half \
    --max-model-len 512
EOF

# Create startup script for vision model (GPU only)
cat > ~/start_vllm_vision.sh << 'EOF'
#!/bin/bash
# Start vLLM with Qwen2-VL vision model (requires GPU)
echo "Starting vLLM server with Qwen2-VL vision model..."
python3 -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-VL-2B-Instruct \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype half \
    --max-model-len 2048
EOF

# Create unified startup script using tmux/screen
cat > ~/start_vllm_all.sh << 'EOF'
#!/bin/bash
# Start all vLLM services using tmux

# Install tmux if not present
if ! command -tmux &> /dev/null; then
    sudo apt-get install -y tmux
fi

# Start tmux session
tmux new-session -d -s vllm "echo 'Starting vLLM services...'"

# Start text embeddings on port 8001
tmux send-keys -t vllm "cd ~ && ./start_vllm_text.sh" C-m

# Start image embeddings on port 8002
tmux send-keys -t vllm "cd ~ && ./start_vllm_image.sh" C-m

echo "All vLLM services started in tmux session 'vllm'"
echo "To attach: tmux attach -t vllm"
echo "To list: tmux ls"
EOF

chmod +x ~/start_vllm_*.sh

echo "=== Setup Complete ==="
echo ""
echo "=== Option 1: CPU-only (t3.large) ==="
echo "  Text embeddings:  cd ~ && ./start_vllm_text.sh (port 8001)"
echo "  Image embeddings: cd ~ && ./start_vllm_image.sh (port 8002)"
echo ""
echo "=== Option 2: GPU (g4dn.xlarge) ==="
echo "  Vision model: cd ~ && ./start_vllm_vision.sh (port 8000)"
echo ""
echo "IMPORTANT: Update .env with the ports you use:"
echo "  For CPU: VLLM_BASE_URL=http://localhost:8001"
echo "  For GPU: VLLM_BASE_URL=http://localhost:8000"
echo ""
echo "For hybrid CPU setup, you would need to configure two separate"
echo "vLLM endpoints or run them sequentially for different tasks."
