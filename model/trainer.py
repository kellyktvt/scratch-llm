from typing import Tuple
from collections import defaultdict
import logging

import torch
from torch.nn import Module
from torch.utils.data import DataLoader
import torch.nn.functional as F
from torch.optim import Adam


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%m-%y %H:%M:%S"
)


def log(step, max_steps, metrics, mode="train"):
    metrics_print = " - ".join([f"{m}: {v[-1]:.3f}" for m, v in metrics.items()])

    if mode == "train":
        print(f"Step {step + 1}/{max_steps} -", metrics_print, end="\r")
    if mode == "eval":
        print(f"\n\Step {step + 1}/{max_steps} -", metrics_print)


def train(
    model: Module,
    ds_train,
    batch_size: int,
    lr: float,
    max_steps: int,
    device: str = DEVICE,
    log_every: int = 10,
) -> Tuple[Module, defaultdict]:
    metrics_tracker = defaultdict(list)
    # val_loss_tracker = defaultdict(list)

    model.to(device)
    optimizer = Adam(model.parameters(), lr=lr)
    model.train()

    for step in range(max_steps):
        inputs, labels = ds_train.get_batch(batch_size)
        inputs, labels = inputs.to(device), labels.to(device)
        logits = model(inputs)

        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), labels.view(-1), ignore_index=-1)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

        metrics_tracker["loss"].append(loss.detach().cpu().item())

        if step % log_every == 0:
            log(step, max_steps, metrics_tracker)

        # val_loss = evaluate(model, dl_val, device)
        # val_loss_tracker["val_loss"].append(val_loss)

    return model, metrics_tracker


@torch.inference_mode()
def evaluate(model: Module, dl_val: DataLoader, device: DEVICE) -> float:
    model.eval()
    running_loss = 0.0
    num_steps = 0

    for sequence, labels in dl_val:
        sequence, labels = sequence.to(device), labels.to(device)
        logits = model(sequence)
        loss = F.cross_entropy(logits.view(-1, logits.size(-1)), labels.view(-1), ignore_index=-1)

        running_loss += loss.cpu().item()
        num_steps += 1

    return loss / num_steps
