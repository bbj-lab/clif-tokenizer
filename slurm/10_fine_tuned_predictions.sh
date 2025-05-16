#!/bin/bash

#SBATCH --job-name=eval-ft-mdl
#SBATCH --output=./output/%A_%a-%x.stdout
#SBATCH --partition=gpuq
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00
#SBATCH --array=0-79

source preamble.sh

div=2
quo=$((SLURM_ARRAY_TASK_ID / div))
rem=$((SLURM_ARRAY_TASK_ID % div))

data_dirs=("${hm}/clif-data" "${hm}/clif-data-ucmc")
models=(
    mdl-llama-orig-58789721-58997654-clsfr-same_admission_death
    mdl-llama-orig-58789721-58997873-clsfr-long_length_of_stay
    mdl-llama-orig-58789721-58997981-clsfr-icu_admission
    mdl-llama-orig-58789721-58998670-clsfr-imv_event
    mdl-llama-large-58788825-58998910-clsfr-same_admission_death
    mdl-llama-large-58788825-58999175-clsfr-long_length_of_stay
    mdl-llama-large-58788825-58999593-clsfr-icu_admission
    mdl-llama-large-58788825-59000154-clsfr-imv_event
    mdl-llama-med-58788824-59002326-clsfr-same_admission_death
    mdl-llama-med-58788824-59013037-clsfr-long_length_of_stay
    mdl-llama-med-58788824-59018866-clsfr-icu_admission
    mdl-llama-med-58788824-59018948-clsfr-imv_event
    mdl-llama-small-58741567-59019015-clsfr-same_admission_death
    mdl-llama-small-58741567-59019016-clsfr-long_length_of_stay
    mdl-llama-small-58741567-59019033-clsfr-icu_admission
    mdl-llama-small-58741567-59019122-clsfr-imv_event
    mdl-llama-smol-58761427-59019126-clsfr-same_admission_death
    mdl-llama-smol-58761427-59019145-clsfr-long_length_of_stay
    mdl-llama-smol-58761427-59019233-clsfr-icu_admission
    mdl-llama-smol-58761427-59019254-clsfr-imv_event
    mdl-llama-tiny-58761428-59019258-clsfr-same_admission_death
    mdl-llama-tiny-58761428-59019266-clsfr-long_length_of_stay
    mdl-llama-tiny-58761428-59019362-clsfr-icu_admission
    mdl-llama-tiny-58761428-59019363-clsfr-imv_event
    mdl-llama-teensy-58741565-58996783-clsfr-imv_event
    mdl-llama-teensy-58741565-59019371-clsfr-same_admission_death
    mdl-llama-teensy-58741565-59019388-clsfr-long_length_of_stay
    mdl-llama-teensy-58741565-59019402-clsfr-icu_admission
    mdl-llama-wee-58996725-59020536-clsfr-same_admission_death
    mdl-llama-wee-58996725-59025304-clsfr-long_length_of_stay
    mdl-llama-wee-58996725-59025432-clsfr-icu_admission
    mdl-llama-wee-58996725-59025505-clsfr-imv_event
    mdl-llama-bitsy-58996726-59025602-clsfr-same_admission_death
    mdl-llama-bitsy-58996726-59026260-clsfr-long_length_of_stay
    mdl-llama-bitsy-58996726-59026270-clsfr-icu_admission
    mdl-llama-bitsy-58996726-59026353-clsfr-imv_event
    mdl-llama-micro-58996720-59000229-clsfr-imv_event
    mdl-llama-micro-58996720-59026365-clsfr-same_admission_death
    mdl-llama-micro-58996720-59026481-clsfr-long_length_of_stay
    mdl-llama-micro-58996720-59026499-clsfr-icu_admission
)

python3 ../src/scripts/fine_tuned_predictions.py \
    --data_dir "${data_dirs[$rem]}" \
    --data_version QC_day_stays_first_24h \
    --model_loc "${hm}/clif-mdls-archive/${models[$quo]}" \
    --outcome "${models[$quo]##*-}"
