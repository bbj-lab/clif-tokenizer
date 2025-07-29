#!/bin/bash

#SBATCH --job-name=add-data
#SBATCH --output=./output/%j-%x.stdout
#SBATCH --partition=tier2q
#SBATCH --time=1:00:00

source preamble.sh

python3 ../fms_ehrs/scripts/add_posthoc_data.py \
    --new_data_loc "${hm}/data-mimic/scratch/en_ner_bc5cdr_md_umls.csv" \
    --new_data_name machine_measurements \
    --data_dir_out "${hm}/data-mimic/" \
    --data_version W \
    --patient_id_col subject_id \
    --time_col ecg_time
