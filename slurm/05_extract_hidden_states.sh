#!/bin/bash

#SBATCH --job-name=extract-states
#SBATCH --output=./output/%A_%a-%x.stdout
#SBATCH --partition=sxmq
#SBATCH --gres=gpu:4
#SBATCH --time=1-00:00:00
#SBATCH --array=0-1

source preamble.sh

div=2
quo=$((SLURM_ARRAY_TASK_ID / div))
rem=$((SLURM_ARRAY_TASK_ID % div))

data_dirs=(
    "${hm}/clif-data"
    "${hm}/clif-data-ucmc"
)
models=(
    llama1b-smol-59946181-hp-QC_noX
)

torchrun --nproc_per_node=4 \
    --rdzv_backend c10d \
    --rdzv-id "$SLURM_ARRAY_TASK_ID" \
    --rdzv-endpoint=localhost:0 \
    ../src/scripts/extract_hidden_states.py \
    --data_dir "${data_dirs[$rem]}" \
    --data_version "${models[$quo]##*-}_first_24h" \
    --model_loc "${hm}/clif-mdls-archive/${models[$quo]}" \
    --batch_sz $((2 ** 5))
