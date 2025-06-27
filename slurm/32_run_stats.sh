#!/bin/bash

#SBATCH --job-name=jumps-inf
#SBATCH --output=./output/%j-%x.stdout
#SBATCH --partition=tier2q
#SBATCH --time=24:00:00

source preamble.sh

data_dirs=(
    "${hm}/clif-data"
    "${hm}/clif-data-ucmc"
)

for d in "${data_dirs[@]}"; do
    python3 ../fms_ehrs/scripts/process_stats.py \
        --data_dir "$d" \
        --data_versions "W++_first_24h" \
        --model_loc "${hm}/clif-mdls-archive/llama-med-60358922_1-hp-W++"
done
