#!/bin/bash
set -e

# Run this from your Mac to launch distributed training on both EC2 instances.
# Usage: bash scripts/launch_training.sh
# Prerequisites: run setup_cluster.sh first

KEY="$HOME/Desktop/distribution-training.pem"
HEAD_IP="16.147.215.138"      # instance 1 public IP
WORKER_IP="34.215.110.131"    # instance 2 public IP

echo "=========================================="
echo "Launching distributed training"
echo "Head:   $HEAD_IP"
echo "Worker: $WORKER_IP"
echo "=========================================="

# Helper: run a command on a remote instance
remote() {
  local ip=$1
  local cmd=$2
  ssh -i "$KEY" -o StrictHostKeyChecking=no ec2-user@"$ip" "$cmd"
}

# Step 1: Check Ray cluster is healthy
echo ""
echo "Step 1: Checking Ray cluster..."
TOTAL_GPUS=$(remote "$HEAD_IP" "source /tmp/sky/bin/activate && python3 -c \"import ray; ray.init(address='auto'); print(int(ray.available_resources().get('GPU', 0)))\"")
echo "Total GPUs in cluster: $TOTAL_GPUS"

if [ "$TOTAL_GPUS" -lt 16 ]; then
  echo "ERROR: Expected 16 GPUs but found $TOTAL_GPUS."
  echo "Re-run setup_cluster.sh to fix the Ray cluster."
  exit 1
fi
echo "Ray cluster OK: 16 GPUs across 2 nodes."

# Step 2: Launch training on head node inside tmux so it survives disconnection
echo ""
echo "Step 2: Launching training on head node..."
remote "$HEAD_IP" "
  tmux new-session -d -s training 2>/dev/null || true
  tmux send-keys -t training '
    cd /home/ec2-user/endless-terminals-playground && \
    bash scripts/train_harbor_qwen3_5_4b_g5_2node.sh
  ' Enter
"

echo ""
echo "=========================================="
echo "Training launched inside tmux on instance 1."
echo ""
echo "To watch the logs:"
echo "  ssh -i $KEY ec2-user@$HEAD_IP"
echo "  tmux attach -t training"
echo ""
echo "To detach from tmux without stopping training:"
echo "  Press Ctrl+B then D"
echo "=========================================="
