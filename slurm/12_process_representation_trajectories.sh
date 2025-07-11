#!/bin/bash

#SBATCH --job-name=process-jumps
#SBATCH --output=./output/%A_%a-%x.stdout
#SBATCH --partition=tier3q
#SBATCH --cpus-per-task=5
#SBATCH --mem=250GB
#SBATCH --time=30:00
#SBATCH --array=0-1

source preamble.sh

case "${SLURM_ARRAY_TASK_ID}" in
    0) data_dir="${hm}/clif-data" ;;
    1) data_dir="${hm}/clif-data-ucmc" ;;
    *) echo "Invalid SLURM_ARRAY_TASK_ID: ${SLURM_ARRAY_TASK_ID}" ;;
esac

python3 ../fms_ehrs/scripts/process_representation_trajectories.py \
    --data_dir "$data_dir" \
    --data_version W++ \
    --model_loc "${hm}/clif-mdls-archive/llama-med-60358922_1-hp-W++" \
    --save_jumps True
