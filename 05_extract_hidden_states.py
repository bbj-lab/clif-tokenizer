#!/usr/bin/env python3

"""
grab the final hidden state (at just under 24h) from each provided sequence
"""

import os
import pathlib

import fire as fi
import numpy as np
import torch as t
import torch.distributed as dist
from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoModelForCausalLM

from logger import get_logger
from vocabulary import Vocabulary

logger = get_logger()
logger.info("running {}".format(__file__))
logger.log_env()


@logger.log_calls
def main(
    *,
    data_dir: os.PathLike = "../clif-data",
    data_version: str = "day_stays_first_24h",
    model_loc: os.PathLike = None,
    batch_sz: int = 2**5,
):
    data_dir, model_loc = map(
        lambda d: pathlib.Path(d).expanduser().resolve(),
        (data_dir, model_loc),
    )

    # prepare parallelism
    is_parallel = t.cuda.device_count() > 1
    if is_parallel:
        dist.init_process_group(backend="nccl")
        rank = dist.get_rank()
    else:
        rank = 0
    device = t.device(f"cuda:{rank}")
    t.cuda.set_device(device)

    # load and prep data
    splits = ("train", "val", "test")
    data_dirs = dict()
    for s in splits:
        data_dirs[s] = data_dir.joinpath(f"{data_version}-tokenized", s)

    vocab = Vocabulary().load(data_dirs["train"].joinpath("vocab.gzip"))

    dataset = (
        load_dataset(
            "parquet",
            data_files={
                s: str(data_dirs[s].joinpath("tokens_timelines.parquet"))
                for s in splits
            },
        )
        .map(lambda batch: {"input_ids": batch["padded"]}, batched=True)
        .with_format("torch")
    )

    # load and prep model
    model = AutoModelForCausalLM.from_pretrained(model_loc)  # in eval mode by default
    d = model.config.hidden_size
    model = model.to(device)
    if is_parallel:
        model = t.nn.parallel.DistributedDataParallel(model, device_ids=[rank])

    # iterate over splits and run inference using model
    stop_tokens = t.tensor([vocab("PAD"), vocab("TRUNC"), vocab("TL_END")]).to(device)
    features = dict()

    for s in splits:
        if rank == 0:
            print(s)
        n = dataset[s].num_rows
        features[s] = np.empty((n, d))
        for batch_idx in tqdm(t.split(t.arange(n), batch_sz)):
            batch = dataset[s]["input_ids"][batch_idx].to(device)
            final_nonpadding_idx = (
                t.argmax(t.isin(batch, stop_tokens).int(), axis=1, keepdim=True) - 1
            )
            with t.inference_mode():
                x = model.forward(input_ids=batch, output_hidden_states=True)
                ret = t.empty(
                    size=(final_nonpadding_idx.size(dim=0), d),
                    dtype=x.hidden_states[-1].dtype,
                    device=device,
                )
                for i, j in enumerate(final_nonpadding_idx):
                    ret[i] = x.hidden_states[-1][i, j, :]
                features[s][batch_idx] = ret.detach().to("cpu")

        np.save(
            data_dirs[s].joinpath("features-{m}.npy".format(m=model_loc.stem)),
            features[s],
        )  # save out result


if __name__ == "__main__":
    fi.Fire(main)
