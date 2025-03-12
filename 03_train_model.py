#!/usr/bin/env python3

"""
train a small model with a packing strategy
"""

import os
import pathlib
import typing

import fire as fi
import torch as t
from transformers import AutoConfig, AutoModelForCausalLM, EarlyStoppingCallback
from trl import SFTConfig, SFTTrainer

from dataset import Datasets
from logger import get_logger

logger = get_logger()
logger.info("running {}".format(__file__))
logger.log_env()


@logger.log_calls
def main(
    *,
    n_epochs: int = 5,
    max_seq_length: int = 1024,
    learning_rate: float = 2e-4,
    data_version: str = "day_stays_qc",
    model_version: str = "llama1b",
    model_name: str = "meta-llama/Llama-3.2-1B",
    per_device_train_batch_size: int = 16,
    per_device_eval_batch_size: int = 16,
    gradient_accumulation_steps=3,
    data_dir: os.PathLike = "../clif-data",
    model_dir: os.PathLike = "../clif-mdls",
    collation: typing.Literal["padded", "packed"] = "packed",
    jid: str = os.getenv("SLURM_JOB_ID", ""),
    wandb_project: str = "clif_mimic_packing",
    **kwargs,
):
    """pass additional model configuration parameters with kwargs"""

    os.environ["HF_HOME"] = "/gpfs/data/bbj-lab/cache/huggingface/"
    os.environ["WANDB_CACHE_DIR"] = "/scratch/burkh4rt/"
    os.environ["WANDB_PROJECT"] = wandb_project
    os.environ["WANDB_RUN_NAME"] = "{m}-{j}".format(m=model_version, j=jid)

    data_dir, model_dir = map(
        lambda d: pathlib.Path(d).expanduser().resolve(),
        (data_dir, model_dir),
    )

    output_dir = model_dir.joinpath("{m}-{j}".format(m=model_version, j=jid))
    output_dir.mkdir(exist_ok=True, parents=True)

    dataset = Datasets(
        data_version=data_version,
        data_dir=data_dir,
        collation=collation,
        max_seq_length=max_seq_length,
    )

    # grab a small mamba for training
    config = AutoConfig.from_pretrained(
        model_name,
        vocab_size=len(dataset.vocab),
        bos_token_id=dataset.vocab("TL_START"),
        eos_token_id=dataset.vocab("TL_END"),
        pad_token_id=dataset.vocab("PAD"),
        **kwargs,
    )
    model = AutoModelForCausalLM.from_config(config)

    max_steps = (
        dataset.n_train
        * n_epochs
        // per_device_train_batch_size
        // t.cuda.device_count()
    )

    # train model
    training_args = SFTConfig(
        report_to="wandb",
        run_name="{m}-{j}".format(m=model_version, j=jid),
        output_dir=str(output_dir),
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,  # simulate larger batch sizes
        learning_rate=learning_rate,  # 2e-4 -- cf. https://arxiv.org/pdf/2412.16178 tbl. 6
        num_train_epochs=1,
        save_total_limit=2,
        metric_for_best_model="eval_loss",
        load_best_model_at_end=True,
        greater_is_better=False,
        eval_strategy="steps",
        save_strategy="best",
        max_steps=max_steps,
        max_seq_length=max_seq_length,
        ddp_find_unused_parameters=False,
    )

    trainer = SFTTrainer(
        model,
        train_dataset=dataset.get_train_dataset(n_epochs=n_epochs),
        eval_dataset=dataset.get_val_dataset(),
        args=training_args,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )
    trainer.train()
    trainer.save_model(
        str(
            output_dir.joinpath(
                "mdl-{d}-{m}-{j}".format(
                    d=data_version,
                    m=model_version,
                    j=jid,
                )
            )
        )
    )


if __name__ == "__main__":
    fi.Fire(main)
