#!/bin/bash

#SBATCH --job-name=vis-over-time
#SBATCH --output=./output/%A_%a-%x.stdout
#SBATCH --partition=tier2q
#SBATCH --time=1:00:00
#SBATCH --array=0-1

source preamble.sh

case "${SLURM_ARRAY_TASK_ID}" in
    0) data_dir="${hm}/data-mimic" ;;
    1) data_dir="${hm}/data-ucmc" ;;
    *) echo "Invalid SLURM_ARRAY_TASK_ID: ${SLURM_ARRAY_TASK_ID}" ;;
esac

python3 ../fms_ehrs/scripts/visualize_tokenwise_predictions.py \
    --data_dir "$data_dir" \
    --out_dir "$hm" \
    --data_version QC_day_stays_first_24h \
    --model_loc "${hm}/mdls-archive/mdl-llama1b-57928921-run1-58115722-clsfr-same_admission_death"
