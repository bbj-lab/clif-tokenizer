#!/bin/bash

#SBATCH --job-name=sft-over-time
#SBATCH --output=./output/%A_%a-%x.stdout
#SBATCH --partition=gpuq
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-1

source preamble.sh

case "${SLURM_ARRAY_TASK_ID}" in
    0) data_dir="${hm}/clif-data" ;;
    1) data_dir="${hm}/clif-data-ucmc" ;;
    *) echo "Invalid SLURM_ARRAY_TASK_ID: ${SLURM_ARRAY_TASK_ID}" ;;
esac

python3 ../fms_ehrs/scripts/sft_predictions_over_time.py \
    --data_dir "$data_dir" \
    --data_version QC_day_stays_first_24h \
    --model_loc "${hm}/clif-mdls-archive/mdl-llama1b-57928921-run1-58115722-clsfr-same_admission_death" \
    --model_loc_urt "${hm}/clif-mdls-archive/mdl-llama1b-57928921-run1-58148405-clsfr-same_admission_death-urt" \
    --n 100
