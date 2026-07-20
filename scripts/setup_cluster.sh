#!/bin/bash
set -e

# Run this from your Mac to set up both EC2 instances in parallel.
# Usage: bash scripts/setup_cluster.sh

KEY="$HOME/Desktop/distribution-training.pem"
HEAD_IP="16.147.215.138"      # instance 1 public IP
WORKER_IP="34.215.110.131"    # instance 2 public IP
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=========================================="
echo "Setting up distributed training cluster"
echo "Head:   $HEAD_IP"
echo "Worker: $WORKER_IP"
echo "=========================================="

# Helper: run a command on a remote instance
remote() {
  local ip=$1
  local cmd=$2
  ssh -i "$KEY" -o StrictHostKeyChecking=no ec2-user@"$ip" "$cmd"
}

# Helper: copy project files to a remote instance
sync_code() {
  local ip=$1
  echo "[$ip] Syncing code..."
  rsync -az --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude 'sky/' --exclude 'data/' \
    -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
    "$PROJECT_DIR/" ec2-user@"$ip":/home/ec2-user/endless-terminals-playground/
  echo "[$ip] Code synced."
}

# Helper: run install_sky.sh on a remote instance
install_on() {
  local ip=$1
  echo "[$ip] Running install_sky.sh..."
  remote "$ip" "cd /home/ec2-user/endless-terminals-playground && bash scripts/install_sky.sh"
  echo "[$ip] Install done."
}

# Step 1: Sync code to both instances in parallel
echo ""
echo "Step 1: Syncing code to both instances..."
sync_code "$HEAD_IP" &
PID1=$!
sync_code "$WORKER_IP" &
PID2=$!
wait $PID1 $PID2
echo "Code sync complete on both instances."

# Step 2: Install dependencies on both instances in parallel
echo ""
echo "Step 2: Installing dependencies on both instances (this takes ~10 min)..."
install_on "$HEAD_IP" > /tmp/install_head.log 2>&1 &
PID1=$!
install_on "$WORKER_IP" > /tmp/install_worker.log 2>&1 &
PID2=$!

# Show progress while waiting
while kill -0 $PID1 2>/dev/null || kill -0 $PID2 2>/dev/null; do
  echo "Still installing... (head log: /tmp/install_head.log, worker log: /tmp/install_worker.log)"
  sleep 30
done
wait $PID1 $PID2
echo "Installation complete on both instances."

# Step 3: Start Ray head on instance 1
echo ""
echo "Step 3: Starting Ray head node on instance 1..."
remote "$HEAD_IP" "source /opt/pytorch/bin/activate && source /tmp/sky/bin/activate && ray stop --force 2>/dev/null; ray start --head --port=6379"
echo "Ray head started."

# Step 4: Start Ray worker on instance 2
echo ""
echo "Step 4: Starting Ray worker on instance 2..."
HEAD_PRIVATE_IP=$(remote "$HEAD_IP" "hostname -I | awk '{print \$1}'")
echo "Head private IP: $HEAD_PRIVATE_IP"
remote "$WORKER_IP" "source /opt/pytorch/bin/activate && source /tmp/sky/bin/activate && ray stop --force 2>/dev/null; ray start --address=${HEAD_PRIVATE_IP}:6379"
echo "Ray worker started."

# Step 5: Verify cluster
echo ""
echo "Step 5: Verifying Ray cluster..."
sleep 5
remote "$HEAD_IP" "source /opt/pytorch/bin/activate && source /tmp/sky/bin/activate && ray status"

echo ""
echo "=========================================="
echo "Cluster setup complete!"
echo "To start training, run:"
echo "  bash scripts/launch_training.sh"
echo "=========================================="
