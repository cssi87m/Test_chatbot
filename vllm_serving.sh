MODEL_NAME="CATI-AI/CMC-Legal-LLM-32B-sft-v2"
MAX_MODEL_LEN=32768

# PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
CUDA_VISIBLE_DEVICES=4,5 \
vllm serve "$MODEL_NAME" \
    --dtype bfloat16 \
    --max-model-len 32768 \
    --port 8010 \
    --tensor-parallel-size 2 \
    --max-num-seqs 6 \
    --max-num-batched-tokens 512 \
    --gpu-memory-utilization 0.95 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes
