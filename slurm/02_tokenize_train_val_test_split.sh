#!/bin/bash

#SBATCH --job-name=tokenize-data
#SBATCH --output=./output/%j-%x.stdout
#SBATCH --partition=tier2q
#SBATCH --mem=100GB
#SBATCH --time=1:00:00

source preamble.sh
export data_version=with_ecg

echo "Processing MIMIC data..."
python3 ../src/scripts/tokenize_train_val_test_split.py \
    --data_dir "${hm}/clif-data/" \
    --data_version_in QC \
    --data_version_out "${data_version:-QC_noX}" \
    --max_padded_len 1024 \
    --day_stay_filter True \
    --include_24h_cut True \
    --drop_nulls_nans True

echo "Using vocab from MIMIC to process UChicago data..."
python3 ../src/scripts/tokenize_train_val_test_split.py \
    --data_dir "${hm}/clif-data-ucmc" \
    --data_version_in QC \
    --data_version_out "${data_version:-QC_noX}" \
    --vocab_path "${hm}/clif-data/${data_version:-QC_noX}-tokenized/train/vocab.gzip" \
    --max_padded_len 1024 \
    --day_stay_filter True \
    --include_24h_cut True \
    --valid_admission_window "('2020-03-01','2022-03-01')" \
    --drop_nulls_nans True
