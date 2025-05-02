#!/usr/bin/env python3

"""
grab the sequence of logits from the test set
"""

import argparse
import collections
import pathlib

import numpy as np
import polars as pl

from src.framework.logger import get_logger
from src.framework.util import (
    extract_examples,
    imshow_text,
    log_summary,
    plot_histograms,
)
from src.framework.vocabulary import Vocabulary

logger = get_logger()
logger.info("running {}".format(__file__))
logger.log_env()

parser = argparse.ArgumentParser()
parser.add_argument("--data_dir_orig", type=pathlib.Path, default="../../clif-data")
parser.add_argument("--name_orig", type=str, default="MIMIC")
parser.add_argument("--data_dir_new", type=pathlib.Path, default="../../clif-data-ucmc")
parser.add_argument("--name_new", type=str, default="UCMC")
parser.add_argument("--data_version", type=str, default="QC_day_stays_first_24h")
parser.add_argument(
    "--model_loc",
    type=pathlib.Path,
    default="../../clif-mdls-archive/llama-med-58788824",
)
parser.add_argument("--out_dir", type=pathlib.Path, default="../../")
parser.add_argument("--n_samp", type=int, default=5)
args, unknowns = parser.parse_known_args()

for k, v in vars(args).items():
    logger.info(f"{k}: {v}")

data_dir_orig, data_dir_new, model_loc, out_dir = map(
    lambda d: pathlib.Path(d).expanduser().resolve(),
    (args.data_dir_orig, args.data_dir_new, args.model_loc, args.out_dir),
)

rng = np.random.default_rng(42)
names = {"orig": args.name_orig, "new": args.name_new}
splits = ("train", "val", "test")
versions = ("orig", "new")
outcomes = ("same_admission_death", "long_length_of_stay", "icu_admission", "imv_event")

data_dirs = collections.defaultdict(dict)
data_dirs["orig"] = {
    s: data_dir_orig.joinpath(f"{args.data_version}-tokenized", s) for s in splits
}
data_dirs["new"] = {
    s: data_dir_new.joinpath(f"{args.data_version}-tokenized", s) for s in splits
}

vocab = Vocabulary().load(data_dirs["orig"]["train"].joinpath("vocab.gzip"))

infm = {
    v: np.load(
        data_dirs[v]["test"].joinpath("log_probs-{m}.npy".format(m=model_loc.stem)),
    )
    / -np.log(2)
    for v in versions
}

tl = {
    v: np.array(
        pl.scan_parquet(
            data_dirs[v]["test"].joinpath(
                "tokens_timelines_outcomes.parquet",
            )
        )
        .select("padded")
        .collect()
        .to_series()
        .to_list()
    )
    for v in versions
}

flags = {
    v: (
        pl.scan_parquet(
            data_dirs[v]["test"].joinpath(
                "tokens_timelines_outcomes.parquet",
            )
        )
        .with_columns(
            [
                pl.when(pl.col(outcome))
                .then(pl.lit(outcome))
                .otherwise(None)
                .alias(outcome)
                for outcome in outcomes
            ]
        )
        .with_columns(flags=pl.concat_str(outcomes, separator=", ", ignore_nulls=True))
        .select("flags")
        .collect()
        .to_series()
        .to_list()
    )
    for v in versions
}

# single-token events
logger.info("Singletons |".ljust(79, "="))
plot_histograms(
    named_arrs={names[v]: infm[v] for v in versions},
    title="Histogram of tokenwise information",
    xaxis_title="bits",
    yaxis_title="frequency",
    savepath=out_dir.joinpath("log_probs-{m}-hist.pdf".format(m=model_loc.stem)),
)
for v in versions:
    logger.info(f"{names[v]}:")
    log_summary(infm[v], logger)
    extract_examples(
        timelines=tl[v], criteria=infm[v], flags=flags[v], vocab=vocab, logger=logger
    )
    logger.info("bottom k")
    # extract_examples(
    #     timelines=tl[v],
    #     criteria=infm[v],
    #     flags=flags[v],
    #     logger=logger,
    #     top_k=False,
    # )


# 2-token events
logger.info("Pairs |".ljust(79, "="))
infm_pairs = {
    v: np.lib.stride_tricks.sliding_window_view(infm[v], window_shape=2, axis=-1).mean(
        axis=-1
    )
    for v in versions
}

plot_histograms(
    named_arrs={names[v]: infm_pairs[v] for v in versions},
    title="Histogram of pairwise information (per token)",
    xaxis_title="bits",
    yaxis_title="frequency",
    savepath=out_dir.joinpath("log_probs_pairs-{m}-hist.pdf".format(m=model_loc.stem)),
)
for v in versions:
    logger.info(f"{names[v]}:")
    log_summary(infm_pairs[v], logger)
    extract_examples(
        timelines=tl[v],
        criteria=infm_pairs[v],
        flags=flags[v],
        vocab=vocab,
        lag=1,
        logger=logger,
    )

# 3-token events
logger.info("Triples |".ljust(79, "="))
infm_trips = {
    v: np.lib.stride_tricks.sliding_window_view(infm[v], window_shape=3, axis=-1).mean(
        axis=-1
    )
    for v in versions
}

plot_histograms(
    named_arrs={names[v]: infm_trips[v] for v in versions},
    title="Histogram of triple information (per token)",
    xaxis_title="bits",
    yaxis_title="frequency",
    savepath=out_dir.joinpath("log_probs_trips-{m}-hist.pdf".format(m=model_loc.stem)),
)
for v in versions:
    logger.info(f"{names[v]}:")
    log_summary(infm_trips[v], logger)
    extract_examples(
        timelines=tl[v],
        criteria=infm_trips[v],
        flags=flags[v],
        vocab=vocab,
        lag=2,
        logger=logger,
    )

n_cols = 2**3
for v in versions:
    samp = rng.choice(infm[v].shape[0], size=args.n_samp, replace=False)
    for i in samp:
        inf = infm[v][i].reshape((-1, n_cols))
        tt = np.array(
            [
                d[:10] if (d := vocab.reverse[t]) is not None else "None"
                for t in tl[v][i]
            ]
        ).reshape((-1, n_cols))
        imshow_text(
            values=inf,
            text=tt,
            title=f"Information by token for patient {i} in {names[v]}",
            savepath=out_dir.joinpath(
                "tokens-{v}-{i}-{m}-hist.pdf".format(v=v, i=i, m=model_loc.stem)
            ),
        )


logger.info("---fin")
