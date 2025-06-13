#!/bin/bash

#SBATCH --job-name=cf-perf-data
#SBATCH --output=./output/%j-%x.stdout
#SBATCH --partition=tier2q
#SBATCH --time=1:00:00

source preamble.sh

data_dirs=(
    "${hm}/clif-data"
    "${hm}/clif-data-ucmc"
)
methods=(
    none
    top
    bottom
    random
)
pct=(10 20 30 40)

for d in "${data_dirs[@]}"; do
    for p in "${pct[@]}"; do

        versions=("W++_first_24h_llama-original-60358922_0-hp-W++_none_20pct")
        handles=("none")

        for me in "${methods[@]:1}"; do
            versions+=("W++_first_24h_llama-original-60358922_0-hp-W++_${me}_${p}pct")
            handles+=("${me}_${p}pct")
        done

        python3 ../fms_ehrs/scripts/aggregate_version_preds.py \
            --data_dir "$d" \
            --data_versions "${versions[@]}" \
            --handles "${handles[@]}" \
            --model_loc "${hm}/clif-mdls-archive/llama-original-60358922_0-hp-W++" \
            --out_dir "${hm}/figs"

    done
done

#models=(
#    llama-original-60358922_0-hp-W++
#    llama-med-60358922_1-hp-W++
#    llama-small-60358922_2-hp-W++
#    llama-smol-60358922_3-hp-W++
#)
#
#for d in "${data_dirs[@]}"; do
#    for mo in "${models[@]}"; do
#
#        versions=()
#        handles=()
#
#        for me in "${methods[@]}"; do
#            versions+=("W++_first_24h_${mo}_${me}_20pct")
#            handles+=("$(echo "$mo" | cut -d'-' -f2)_${me}")
#        done
#
#        python3 ../fms_ehrs/scripts/aggregate_version_preds.py \
#            --data_dir "$d" \
#            --data_versions "${versions[@]}" \
#            --handles "${handles[@]}" \
#            --model_loc "${hm}/clif-mdls-archive/${mo}" \
#            --out_dir "${hm}/figs"
#
#    done
#done
