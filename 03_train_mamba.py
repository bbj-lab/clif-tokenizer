#!/usr/bin/env python3

"""
train a small version of Mamba on our tokenized & padded data
"""

import os
import pathlib

data_version = "day_stays_qc"
model_version = "medium"
hm = pathlib.Path("/gpfs/data/bbj-lab/users/burkh4rt/").expanduser().absolute()
jid = os.getenv("SLURM_JOB_ID", "")

os.environ["HF_HOME"] = "/gpfs/data/bbj-lab/cache/huggingface/"
os.environ["WANDB_CACHE_DIR"] = "/scratch/burkh4rt/"
os.environ["WANDB_DIR"] = "/scratch/burkh4rt/"
os.environ["WANDB_PROJECT"] = "mamba_clif_mimic_qc"

from datasets import Features, Sequence, Value, load_dataset
from transformers import AutoConfig, AutoModelForCausalLM
from trl import SFTConfig, SFTTrainer

from logger import get_logger
from vocabulary import Vocabulary

if os.getenv("RANK", "0") == "0":
    logger = get_logger()
    logger.info("running {}".format(__file__))

# locate data and vocab
splits = ("train", "val")
data_dirs = {
    s: hm.joinpath("clif-data", f"{data_version}-tokenized", s) for s in splits
}
vocab = Vocabulary().load(data_dirs["train"].joinpath("vocab.gzip"))
output_dir = hm.joinpath("clif-mdls", model_version)
output_dir.mkdir(exist_ok=True, parents=True)

# grab a small mamba for training
model_name = "state-spaces/mamba-370m-hf"
config = AutoConfig.from_pretrained(
    model_name,
    vocab_size=len(vocab),
    bos_token_id=vocab("TL_START"),
    eos_token_id=[vocab("TL_END"), vocab("TRUNC")],
    pad_token_id=vocab("PAD"),
)
model = AutoModelForCausalLM.from_config(config)

# load data
dataset = (
    load_dataset(
        "parquet",
        data_files={
            s: str(data_dirs[s].joinpath("tokens_timelines.parquet"))
            for s in ("train", "val")
        },
    )
    .map(
        lambda batch: {"input_ids": batch["padded"]},
        batched=True,
        remove_columns=["hospitalization_id", "tokens", "times", "seq_len", "padded"],
        features=Features({"input_ids": Sequence(Value("uint8"))}),
    )
    .shuffle(seed=42)
)

# train model
training_args = SFTConfig(
    report_to="wandb",
    run_name="{m}-{j}".format(m=model_version, j=jid),
    max_seq_length=1024,
    output_dir=str(output_dir),
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    gradient_accumulation_steps=1,  # simulate larger batch sizes
    learning_rate=2e-4,  # 2e-4 -- cf. https://arxiv.org/pdf/2412.16178 tbl. 6
    num_train_epochs=1,
    save_total_limit=2,
    load_best_model_at_end=True,
    # neftune_noise_alpha=5,
    eval_strategy="steps",
    save_strategy="steps",
)
trainer = SFTTrainer(
    model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["val"],
    args=training_args,
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
