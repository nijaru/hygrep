"""Common constants and utilities for embedders."""

import numpy as np

# snowflake-arctic-embed-s: 33M params, 384 dims, Apache 2.0
# BERT-based architecture (e5-small-unsupervised), fast inference
# ViDoRe V3: competitive with 100M+ models despite small size
MODEL_REPO = "Snowflake/snowflake-arctic-embed-s"
MODEL_FILE_FP16 = "onnx/model_fp16.onnx"  # ~67 MB - for GPU
MODEL_FILE_INT8 = "onnx/model_int8.onnx"  # ~34 MB - for CPU
TOKENIZER_FILE = "tokenizer.json"
DIMENSIONS = 384
MAX_LENGTH = 512  # snowflake supports 512 tokens
BATCH_SIZE = 64  # smaller model allows larger batches
MODEL_VERSION = "snowflake-arctic-embed-s-v1"  # For manifest migration tracking

# Query prefix for optimal retrieval (documents don't need prefix)
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Query cache configuration
QUERY_CACHE_MAX_SIZE = 128


def evict_cache(cache: dict[str, np.ndarray]) -> None:
    """Evict oldest half of cache entries."""
    keys = list(cache.keys())[: len(cache) // 2]
    for k in keys:
        del cache[k]
