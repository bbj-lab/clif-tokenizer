#!/bin/bash

#SBATCH --job-name=examine-mdl
#SBATCH --output=./output/%j-%x.stdout
#SBATCH --partition=gpuq
#SBATCH --gres=gpu:1
#SBATCH --time=1:00:00

hm="/gpfs/data/bbj-lab/users/$(whoami)"
cd "${hm}/clif-tokenizer" || exit
source ~/.bashrc
source venv/bin/activate
python3 04_examine_model.py \
    --projector_type PCA \
    --data_dir "${hm}/clif-data" \
    --data_version QC_day_stays \
    --model_loc "${hm}/clif-mdls-archive/llama1b-57928921-run1" \
    --out_dir "${hm}"
