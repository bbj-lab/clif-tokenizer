#!/usr/bin/env python3

"""
utility functions
"""

import collections
import logging
import os
import pathlib
import typing

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import sklearn.calibration as skl_cal
import sklearn.metrics as skl_mets
import torch as t

from src.framework.logger import get_logger
from src.framework.vocabulary import Vocabulary

Pathlike: typing.TypeAlias = pathlib.PurePath | str | os.PathLike
Dictlike: typing.TypeAlias = collections.OrderedDict | dict

pio.kaleido.scope.mathjax = None

mains = ("#EAAA00", "#DE7C00", "#789D4A", "#275D38", "#007396", "#56315F", "#A4343A")
lights = ("#F3D03E", "#ECA154", "#A9C47F", "#9CAF88", "#3EB1C8", "#86647A", "#B46A55")
darks = ("#CC8A00", "#A9431E", "#13301C", "#284734", "#002A3A", "#41273B", "#643335")
colors = mains + lights + darks


def mvg_avg(x: np.array, w: int = 4) -> np.array:
    """
    moving average for flat array `x` with window size `w`;
    returns array of same length as x
    """
    assert w >= 1
    x_aug = np.concatenate(([x[0]] * (w - 1), x))
    return np.lib.stride_tricks.sliding_window_view(x_aug, w).mean(axis=-1)


def rt_padding_to_left(
    t_rt_pdd: t.Tensor, pd_tk: int, unif_rand_trunc: bool = False
) -> t.Tensor:
    """
    take a tensor `t_rt_pdd` padded on the right with padding token `pd_tk` and
    move that padding to the left; if `unif_rand_trunc`, truncate sequence
    uniformly at random
    """
    i = t.argmax(
        (t_rt_pdd == pd_tk).int()
    ).item()  # either the index of the first padding token or 0
    if unif_rand_trunc and i > 0:
        i = t.randint(
            low=1, high=i, size=(1,)
        ).item()  # new cut-point chosen uniformly at random from seq length
    return (
        t.concat([t.full((t_rt_pdd.shape[0] - i,), pd_tk), t_rt_pdd[:i]])
        if i > 0
        else t_rt_pdd  # if no padding was present
    )


def log_classification_metrics(
    y_true: np.array, y_score: np.array, logger: logging.Logger
):
    """evaluate a classifier under a variety of metrics"""
    assert y_true.shape[0] == y_score.shape[0]

    logger.info(
        "roc_auc: {:.3f}".format(skl_mets.roc_auc_score(y_true=y_true, y_score=y_score))
    )

    for met in (
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
    ):
        logger.info(
            "{}: {:.3f}".format(
                met,
                getattr(skl_mets, f"{met}_score")(
                    y_true=y_true, y_pred=np.round(y_score)
                ),
            )
        )


def plot_calibration_curve(
    named_results: Dictlike, n_bins: int = 10, savepath: Pathlike = None
):
    """
    plot a calibration curve for each named set of predictions;
    {"name": {"y_true": y_true, "y_score": y_score}}
    if provided a `savepath`; otherwise, display
    """

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect Calibration",
            line=dict(dash="dash", color="gray"),
        )
    )

    for i, (name, results) in enumerate(named_results.items()):

        y_true = results["y_true"]
        y_score = results["y_score"]

        assert y_true.shape[0] == y_score.shape[0]

        prob_true, prob_pred = skl_cal.calibration_curve(y_true, y_score, n_bins=n_bins)

        fig.add_trace(
            go.Scatter(
                x=prob_pred,
                y=prob_true,
                mode="lines+markers",
                name=name,
                marker=dict(color=colors[i % len(colors)]),
            )
        )

    fig.update_layout(
        title="Calibration Curve",
        xaxis_title="Mean Predicted Probability",
        yaxis_title="Fraction of Positives",
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
        template="plotly_white",
    )

    if savepath is None:
        fig.show()
    else:
        fig.write_image(pathlib.Path(savepath).expanduser().resolve())


def plot_roc_curve(named_results: Dictlike, savepath: Pathlike = None):
    """
    plot a ROC curve for each named set of predictions;
    {"name": {"y_true": y_true, "y_score": y_score}}
    if provided a `savepath`; otherwise, display
    """

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Chance",
            line=dict(dash="dash", color="gray"),
        )
    )

    for i, (name, results) in enumerate(named_results.items()):

        y_true = results["y_true"]
        y_score = results["y_score"]

        assert y_true.shape[0] == y_score.shape[0]

        fpr, tpr, _ = skl_mets.roc_curve(y_true, y_score)

        fig.add_trace(
            go.Scatter(
                x=fpr,
                y=tpr,
                mode="lines+markers",
                name="{} (AUC: {:.3f})".format(
                    name, skl_mets.roc_auc_score(y_true=y_true, y_score=y_score)
                ),
                marker=dict(color=colors[(i + 1) % len(colors)], size=1),
            )
        )

    fig.update_layout(
        title="Receiver operating characteristic",
        xaxis_title="False positive rate",
        yaxis_title="True positive rate",
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
        template="plotly_white",
    )

    if savepath is None:
        fig.show()
    else:
        fig.write_image(pathlib.Path(savepath).expanduser().resolve())


def plot_precision_recall_curve(
    named_results: Dictlike, savepath: Pathlike = None, decimals: int = 3
):
    """
    plot a precision-recall curve for each named set of predictions;
    {"name": {"y_true": y_true, "y_score": y_score}}
    if provided a `savepath`; otherwise, display
    """

    fig = go.Figure()

    for i, (name, results) in enumerate(named_results.items()):

        y_true = results["y_true"]
        y_score = results["y_score"]

        assert y_true.shape[0] == y_score.shape[0]

        precs, recs, _ = skl_mets.precision_recall_curve(
            y_true, np.round(y_score, decimals=decimals), drop_intermediate=True
        )

        fig.add_trace(
            go.Scatter(
                x=recs,
                y=precs,
                mode="lines+markers",
                name="{} (PR-AUC: {:.3f})".format(name, skl_mets.auc(recs, precs)),
                marker=dict(color=colors[(i + 1) % len(colors)], size=1),
            )
        )

    fig.update_layout(
        title="Precision-recall curve",
        xaxis_title="Recall",
        yaxis_title="Precision",
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
        template="plotly_white",
    )

    if savepath is None:
        fig.show()
    else:
        fig.write_image(pathlib.Path(savepath).expanduser().resolve())


def plot_histogram(
    arr: np.array, title: str = "Histogram", nbins: int = 50, savepath: Pathlike = None
):
    """
    plot a histogram of the non-nan values in an array `arr`;
    if provided a `savepath`; otherwise, display
    """

    fig = px.histogram(
        arr[np.isfinite(arr)].ravel(), nbins=nbins, labels={"value": "Value"}
    )

    fig.update_layout(title=title, template="plotly_white", showlegend=False)

    if savepath is None:
        fig.show()
    else:
        fig.write_image(pathlib.Path(savepath).expanduser().resolve())


def plot_histograms(
    named_arrs: dict,
    *,
    title: str = "Histogram",
    nbins: int = 50,
    savepath: Pathlike = None,
    **kwargs,
):
    """
    plot a histogram of the non-nan values in an array `arr`;
    if provided a `savepath`; otherwise, display;
    NB: by default, plotly saves all data passed to its histogram function--not simply
    the summary statistics required to create the plot
    """

    fig = go.Figure()

    edges = np.histogram_bin_edges(
        np.concatenate([x[np.isfinite(x)].ravel() for x in named_arrs.values()]),
        bins=nbins,
    )

    for i, (name, arr) in enumerate(named_arrs.items()):
        ct, bins = np.histogram(arr[np.isfinite(arr)].ravel(), bins=edges, density=True)
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        bin_widths = bins[1:] - bins[:-1]
        fig.add_trace(
            go.Bar(
                x=bin_centers,
                y=ct,
                name=name,
                opacity=0.5,
                width=bin_widths,
                marker_color=colors[(i + 1) % len(colors)],
            )
        )
        # fig.add_trace(
        #     go.Histogram(
        #         x=arr[np.isfinite(arr)].ravel(),
        #         nbinsx=nbins,
        #         name=name,
        #         opacity=0.5,
        #         marker_color=colors[(i + 1) % len(colors)],
        #     )
        # )
    fig.update_layout(barmode="overlay", template="plotly_white", title=title, **kwargs)
    # df = pd.DataFrame(
    #     [(n, x) for n, arr in named_arrs.items() for x in arr[np.isfinite(arr)]],
    #     columns=["name", "value"],
    # )
    #
    # fig = px.histogram(
    #     df,
    #     x="value",
    #     color="name",
    #     nbins=nbins,
    #     opacity=0.5,
    #     color_discrete_sequence=colors[1:],
    #     barmode="overlay",
    #     template="plotly_white",
    #     title=title,
    # )

    if savepath is None:
        fig.show()
    else:
        fig.write_image(pathlib.Path(savepath).expanduser().resolve())


def log_summary(arr: np.array, logger: logging.Logger):
    """log some summary stats for the array `arr`"""
    logger.info("Array of shape: {}".format(arr.shape))
    logger.info("Pct non-nan: {:.2f}".format(100 * np.isfinite(arr).mean()))
    logger.info("Range: ({:.2f}, {:.2f})".format(np.nanmin(arr), np.nanmax(arr)))
    logger.info("Mean: {:.2f}".format(np.nanmean(arr)))
    for q in (0.5, 0.9, 0.99, 0.999, 0.9999):  # 0.0001, 0.001, 0.01, 0.1,
        logger.info(
            "{:05.2f}% quantile: {:.2f}".format(100 * q, np.nanquantile(arr, q))
        )


def ragged_lists_to_array(ls_arr: list[np.array]) -> np.array:
    """
    form an 2d-array from a collection of variably-sized 1d-arrays
    """
    n, m = len(ls_arr), max(map(len, ls_arr))
    arr = np.full(shape=(n, m), fill_value=np.nan)
    for i, x in enumerate(ls_arr):
        arr[i, : len(x)] = x
    return arr


def extract_examples(
    timelines: np.array,
    criteria: np.array,
    vocab: Vocabulary,
    flags: list = None,
    k: int = 10,
    w_sz: int = 3,
    lag: int = 0,
    logger: logging.Logger = get_logger(),
    top_k: bool = True,
):
    assert timelines.shape[0] == criteria.shape[0]
    assert timelines.shape[1] == criteria.shape[1] + lag
    if flags:
        assert len(flags) == timelines.shape[0]
    top_k_flat_idx = (
        np.argsort(np.nan_to_num(criteria.flatten()))[::-1][:k]
        if top_k
        else np.argsort(np.nan_to_num(criteria.flatten(), nan=np.inf))[:k]  # bottom k
    )
    top_k_idx = np.array(np.unravel_index(top_k_flat_idx, criteria.shape)).T
    m = timelines.shape[-1]
    for i0, i1 in top_k_idx:
        ints = timelines[i0, max(0, i1 - w_sz) : min(m - 1, i1 + w_sz + lag)]
        tkns = "->".join(
            s if (s := vocab.reverse[i]) is not None else "None" for i in ints
        )
        hit = " ".join(
            s if (s := vocab.reverse[i]) is not None else "None"
            for i in timelines[i0][i1 : i1 + lag + 1]
        )
        if flags:
            logger.info(f"{i0=}, {i1=} | {flags[i0]}")
        else:
            logger.info(f"{i0=}, {i1=} ")
        logger.info(f"{hit=} in {tkns}")
        logger.info(
            "->".join(
                map(
                    str,
                    criteria[i0, max(0, i1 - w_sz) : min(m - 1, i1 + w_sz + lag)].round(
                        2
                    ),
                )
            )
        )


def imshow_text(values: np.array, text: np.array, title: str = "", savepath=None):
    assert values.shape == text.shape
    fig = go.Figure(
        data=go.Heatmap(
            z=values,
            text=text,
            texttemplate="%{text}",
            textfont={"size": 12, "color": "white"},
            colorscale="Viridis",
            reversescale=False,
            showscale=True,
            zsmooth=False,
            xgap=1,
            ygap=1,
        )
    )

    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False, autorange="reversed"
        ),
        height=1800,
        width=900,
    )

    if savepath is None:
        fig.show()
    else:
        fig.write_image(pathlib.Path(savepath).expanduser().resolve())


def set_pd_options():
    pd.options.display.float_format = "{:,.3f}".format
    pd.options.display.max_columns = None
    pd.options.display.width = 250
    pd.options.display.max_colwidth = 100


if __name__ == "__main__":
    logger = get_logger()
    np_rng = np.random.default_rng(42)

    print(ragged_lists_to_array([[2.0, 3.0], [3.0]]))

    y_seed = np_rng.uniform(size=1000)
    y_true = (y_seed > 0.4).astype(int)
    y_pred = np.clip(y_seed + np_rng.normal(scale=0.2, size=1000), a_min=0, a_max=1)
    y_pred2 = np.clip(y_seed + np_rng.normal(scale=0.2, size=1000), a_min=0, a_max=1)
    y_pred3 = np.clip(y_seed + np_rng.normal(scale=0.5, size=1000), a_min=0, a_max=1)
    log_classification_metrics(y_true, y_pred, logger)

    named_results = collections.OrderedDict()
    named_results["test1"] = {"y_true": y_true, "y_score": y_pred}
    named_results["test2"] = {"y_true": y_true, "y_score": y_pred2}
    named_results["test3"] = {"y_true": y_true, "y_score": y_pred3}

    plot_calibration_curve(named_results)
    plot_roc_curve(named_results)
    plot_precision_recall_curve(named_results)

    vals = np_rng.normal(scale=0.2, size=100000).reshape((10, 10, -1))
    vals[vals > 0.6] = np.nan
    plot_histogram(vals)
    log_summary(vals, logger)

    plot_histograms({"foo": vals, "bar": vals + 0.2}, xaxis_title="bits")

    n_tot, n_col = 2**10, 2**3
    vals = np_rng.poisson(lam=20, size=n_tot).reshape((-1, n_col))
    text = np.arange(n_tot).astype(str).reshape((-1, n_col))
    imshow_text(values=vals, text=text)
