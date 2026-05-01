FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install --upgrade pip && \
    pip3 install pytest pyzmq pandas scikit-learn pyarrow

RUN mkdir -p /home/user/pipeline /home/user/data && \
    chmod 0777 /home/user && \
    chmod 0777 /home/user/pipeline && \
    chmod 0777 /home/user/data

RUN cat << 'EOF' > /home/user/pipeline/coordinator.py
#!/usr/bin/env python3
"""
Coordinator for distributed tf-idf feature extraction.
Pushes chunks to workers via ZeroMQ, collects results, aggregates.
"""
import pickle
import time
import zmq
import pandas as pd

def main():
    context = zmq.Context()

    # Socket to send work to workers
    sender = context.socket(zmq.PUSH)
    sender.bind("tcp://127.0.0.1:5557")

    # Socket to receive results from workers
    receiver = context.socket(zmq.PULL)
    receiver.bind("tcp://127.0.0.1:5558")

    # Load data
    df = pd.read_parquet("/home/user/data/raw.parquet")

    # Split into chunks of 1000 rows
    chunk_size = 1000
    chunks = [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
    num_chunks = len(chunks)

    print(f"Coordinator: Sending {num_chunks} chunks to workers")

    # Send all chunks immediately (BUG: workers may not be connected yet)
    for chunk_id, chunk in enumerate(chunks):
        msg = pickle.dumps((chunk_id, chunk))
        sender.send(msg)
        print(f"Coordinator: Sent chunk {chunk_id}")

    # Collect results (BUG: using list, not dict - duplicates possible)
    results = []
    receiver.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second timeout

    try:
        while True:
            try:
                msg = receiver.recv()
                chunk_id, result_df = pickle.loads(msg)
                results.append(result_df)
                print(f"Coordinator: Received result for chunk {chunk_id}")
            except zmq.Again:
                print("Coordinator: Timeout waiting for results, finishing up")
                break
    except Exception as e:
        print(f"Coordinator: Error receiving: {e}")

    # Aggregate results (BUG: concat with misaligned columns from different vocabularies)
    if results:
        final_df = pd.concat(results, ignore_index=True)
        final_df = final_df.fillna(0)
        final_df.to_parquet("/home/user/data/features.parquet")
        print(f"Coordinator: Saved {len(final_df)} rows to features.parquet")
    else:
        print("Coordinator: No results received!")

    sender.close()
    receiver.close()
    context.term()

if __name__ == "__main__":
    main()
EOF

RUN cat << 'EOF' > /home/user/pipeline/worker.py
#!/usr/bin/env python3
"""
Worker for distributed tf-idf feature extraction.
Receives chunks from coordinator, computes tf-idf, sends results back.
"""
import pickle
import sys
import zmq
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def main():
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "0"

    context = zmq.Context()

    # Socket to receive work from coordinator
    receiver = context.socket(zmq.PULL)
    receiver.connect("tcp://127.0.0.1:5557")

    # Socket to send results to coordinator
    sender = context.socket(zmq.PUSH)
    sender.connect("tcp://127.0.0.1:5558")

    print(f"Worker {worker_id}: Started and connected")

    chunks_processed = 0

    # BUG: Each worker creates its own vectorizer with its own vocabulary
    vectorizer = TfidfVectorizer(max_features=100)

    while True:
        try:
            msg = receiver.recv()
            chunk_id, chunk_df = pickle.loads(msg)

            print(f"Worker {worker_id}: Processing chunk {chunk_id}")

            # Compute tf-idf (BUG: fitting on each chunk independently)
            texts = chunk_df["text"].tolist()
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Convert to DataFrame with feature names as columns
            feature_names = vectorizer.get_feature_names_out()
            result_df = pd.DataFrame(
                tfidf_matrix.toarray(),
                columns=feature_names
            )

            # Send result back
            result_msg = pickle.dumps((chunk_id, result_df))
            sender.send(result_msg)

            chunks_processed += 1
            print(f"Worker {worker_id}: Processed chunk {chunk_id} (total: {chunks_processed})")

        except Exception as e:
            print(f"Worker {worker_id}: Error: {e}")
            break

    receiver.close()
    sender.close()
    context.term()

if __name__ == "__main__":
    main()
EOF

RUN cat << 'EOF' > /home/user/pipeline/run.sh
#!/bin/bash
# Run the distributed feature extraction pipeline

cd /home/user/pipeline

# Start coordinator in background
python3 coordinator.py &
COORD_PID=$!

# Start 3 workers
python3 worker.py 1 &
WORKER1_PID=$!
python3 worker.py 2 &
WORKER2_PID=$!
python3 worker.py 3 &
WORKER3_PID=$!

# Wait for coordinator to finish
wait $COORD_PID
COORD_EXIT=$?

# Kill workers (they spin forever waiting for more work)
kill $WORKER1_PID $WORKER2_PID $WORKER3_PID 2>/dev/null

exit $COORD_EXIT
EOF

RUN cat << 'EOF' > /home/user/pipeline/single.py
#!/usr/bin/env python3
"""
Single-threaded reference implementation for tf-idf feature extraction.
This produces correct output but is slow.
"""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def main():
    # Load data
    df = pd.read_parquet("/home/user/data/raw.parquet")
    print(f"Loaded {len(df)} rows")

    # Compute tf-idf on all data with single vocabulary
    vectorizer = TfidfVectorizer(max_features=100)
    texts = df["text"].tolist()
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Convert to DataFrame
    feature_names = vectorizer.get_feature_names_out()
    result_df = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=feature_names
    )

    # Save
    result_df.to_parquet("/home/user/data/features_reference.parquet")
    print(f"Saved {len(result_df)} rows to features_reference.parquet")

    # Verify values are in valid range
    max_val = result_df.values.max()
    min_val = result_df.values.min()
    print(f"Value range: [{min_val}, {max_val}]")
    assert min_val >= 0.0, "Negative tf-idf values!"
    assert max_val <= 1.0, "tf-idf values > 1!"

if __name__ == "__main__":
    main()
EOF

RUN chmod +x /home/user/pipeline/run.sh && \
    chmod 0666 /home/user/pipeline/coordinator.py && \
    chmod 0666 /home/user/pipeline/worker.py && \
    chmod 0777 /home/user/pipeline/run.sh && \
    chmod 0666 /home/user/pipeline/single.py

RUN python3 << 'PYSCRIPT'
import pandas as pd
import random
import string

random.seed(42)

# Generate 50,000 text samples
words = [
    "data", "science", "machine", "learning", "deep", "neural", "network",
    "algorithm", "model", "training", "feature", "extraction", "vector",
    "matrix", "tensor", "gradient", "descent", "optimization", "loss",
    "function", "activation", "layer", "batch", "epoch", "accuracy",
    "precision", "recall", "classification", "regression", "clustering",
    "python", "pandas", "numpy", "sklearn", "tensorflow", "pytorch",
    "analysis", "processing", "pipeline", "distributed", "parallel",
    "computing", "memory", "storage", "database", "query", "index",
    "performance", "scalability", "efficiency", "throughput", "latency",
    "cloud", "server", "container", "kubernetes", "docker", "microservice",
    "api", "rest", "json", "xml", "http", "request", "response",
    "authentication", "authorization", "security", "encryption", "hash",
    "testing", "debugging", "logging", "monitoring", "alerting", "metrics",
    "visualization", "dashboard", "report", "insight", "trend", "pattern",
    "customer", "user", "product", "service", "business", "revenue",
    "marketing", "sales", "support", "feedback", "satisfaction", "retention"
]

texts = []
for i in range(50000):
    # Generate random text with 10-50 words
    num_words = random.randint(10, 50)
    text_words = random.choices(words, k=num_words)
    # Add some unique words to create variety
    for _ in range(random.randint(1, 5)):
        unique_word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        text_words.insert(random.randint(0, len(text_words)), unique_word)
    texts.append(' '.join(text_words))

df = pd.DataFrame({"text": texts})
df.to_parquet("/home/user/data/raw.parquet", index=False)
print(f"Created raw.parquet with {len(df)} rows")
PYSCRIPT

RUN chown -R 1000:1000 /home/user && \
    chmod -R 0777 /home/user

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
