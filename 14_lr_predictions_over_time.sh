#!/bin/bash

#SBATCH --job-name=add-lr-over-time
#SBATCH --output=./output/%j-%x.stdout
#SBATCH --partition=tier3q
#SBATCH --mem=1TB
#SBATCH --time=24:00:00
#SBATCH --array=0-1

source preamble.sh

echo "SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"

case "${SLURM_ARRAY_TASK_ID}" in
    0) data_dir="${hm}/clif-data" ;;
    1) data_dir="${hm}/clif-data-ucmc" ;;
    *) echo "Invalid SLURM_ARRAY_TASK_ID: ${SLURM_ARRAY_TASK_ID}" ;;
esac

python3 -i "13_lr_predictions_over_time.py" \
    --data_dir_train "$data_dir" \
    --data_dir_pred "$data_dir" \
    --data_version QC_day_stays_first_24h \
    --model_loc_base "${hm}/clif-mdls-archive/llama1b-57928921-run1" \
    --model_loc_sft "${hm}/clif-mdls-archive/mdl-llama1b-57928921-run1-58115722-clsfr-same_admission_death" \
    --big_batch_sz $((2 ** 12))
