#!/bin/bash

#SBATCH --job-name=tune-mdl
#SBATCH --output=./output/%j-%x.stdout
#SBATCH --partition=gpuq
#SBATCH --gres=gpu:8
#SBATCH --array=0-5

source preamble.sh

echo "SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"

names=(1B med small smol tiny teensy)
hidden_sizes=(2048 1024 512 256 128 64)
intermediate_sizes=(8192 2048 1024 512 256 128)

torchrun --nproc_per_node=8 \
    ../src/scripts/tune_model.py \
    --n_epochs 5 \
    --n_trials 10 \
    --data_dir "${hm}/clif-data" \
    --data_version QC_day_stays \
    --collation packed \
    --model_dir "${hm}/clif-mdls" \
    --model_version "llama1b-${names[$SLURM_ARRAY_TASK_ID]}" \
    --model_name "meta-llama/Llama-3.2-1B" \
    --wandb_project llama-sizing \
    --hidden_size "${hidden_sizes[$SLURM_ARRAY_TASK_ID]}" \
    --intermediate_size "${intermediate_sizes[$SLURM_ARRAY_TASK_ID]}" \
    --num_hidden_layers $((2 ** 3)) \
    --num_attention_heads $((2 ** 3))
