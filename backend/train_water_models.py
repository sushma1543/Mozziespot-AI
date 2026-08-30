"""Train and evaluate water-segmentation models on Sen1Floods11 GeoTIFF pairs."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from app.ai.deeplabv3plus import DeepLabV3PlusLite
from app.ai.segformer import SegFormerLite
from app.ai.unet import UNet
from app.services.validation_service import calibration_bins, segmentation_metrics, threshold_curves

BANDS = (1, 2, 3, 4, 8, 12)  # Blue, green, red, red-edge, NIR and SWIR-2.


def find_pairs(root: Path) -> list[tuple[Path, Path]]:
    images = {path.name.replace("_S2Hand.tif", ""): path for path in root.rglob("*_S2Hand.tif")}
    labels = {path.name.replace("_LabelHand.tif", ""): path for path in root.rglob("*_LabelHand.tif")}
    pairs = [(images[key], labels[key]) for key in sorted(images.keys() & labels.keys())]
    if len(pairs) < 10:
        raise RuntimeError(f"Only {len(pairs)} image/label pairs found; at least 10 are required")
    return pairs


def event_name(path: Path) -> str:
    return path.name.split("_", 1)[0]


def split_by_event(pairs: list[tuple[Path, Path]], seed: int) -> dict[str, list[tuple[Path, Path]]]:
    events = sorted({event_name(image) for image, _ in pairs})
    random.Random(seed).shuffle(events)
    train_end = max(1, round(len(events) * 0.7))
    validation_end = max(train_end + 1, round(len(events) * 0.85))
    assignments = {
        event: "training" if index < train_end else "validation" if index < validation_end else "test"
        for index, event in enumerate(events)
    }
    result = {"training": [], "validation": [], "test": []}
    for pair in pairs:
        result[assignments[event_name(pair[0])]].append(pair)
    if not result["test"]:
        result["test"].append(result["validation"].pop())
    return result


class WaterDataset(Dataset):
    def __init__(self, pairs: list[tuple[Path, Path]], augment: bool = False):
        self.pairs = pairs
        self.augment = augment

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, index):
        image_path, label_path = self.pairs[index]
        with rasterio.open(image_path) as source:
            image = source.read(BANDS).astype("float32")
        with rasterio.open(label_path) as source:
            label = source.read(1).astype("float32")
        valid = label >= 0
        label = np.where(label == 1, 1, 0).astype("float32")
        image = np.nan_to_num(image / 10_000.0, nan=0.0, posinf=1.0, neginf=0.0)
        image = np.clip(image, 0, 1)
        if self.augment and random.random() < 0.5:
            image, label, valid = image[:, :, ::-1].copy(), label[:, ::-1].copy(), valid[:, ::-1].copy()
        return torch.from_numpy(image), torch.from_numpy(label[None]), torch.from_numpy(valid[None])


class MaskedBCEDice(nn.Module):
    def forward(self, probability, target, valid):
        target = target.to(dtype=probability.dtype)
        valid = valid.bool()
        if not valid.any():
            return probability.sum() * 0
        probability = probability.clamp(1e-6, 1 - 1e-6)
        selected_probability, selected_target = probability[valid], target[valid]
        bce = nn.functional.binary_cross_entropy(selected_probability, selected_target)
        intersection = (selected_probability * selected_target).sum()
        dice_loss = 1 - (2 * intersection + 1) / (selected_probability.sum() + selected_target.sum() + 1)
        return bce + dice_loss


def make_model(name: str):
    if name == "unet":
        return UNet(in_channels=6, out_channels=1)
    if name == "deeplabv3plus":
        return DeepLabV3PlusLite(in_channels=6, classes=1)
    if name == "segformer":
        return SegFormerLite(in_channels=6, classes=1)
    raise ValueError(f"Unknown model: {name}")


def evaluate(model, loader, device):
    truth, scores, losses = [], [], []
    criterion = MaskedBCEDice()
    model.eval()
    with torch.no_grad():
        for image, target, valid in loader:
            image, target, valid = image.to(device), target.to(device), valid.to(device).bool()
            probability = model(image)
            losses.append(float(criterion(probability, target, valid)))
            truth.extend(target[valid].cpu().numpy().astype("uint8").tolist())
            scores.extend(probability[valid].cpu().numpy().tolist())
    predicted = [int(value >= 0.5) for value in scores]
    return {
        "loss": round(float(np.mean(losses)), 6),
        "metrics": segmentation_metrics(truth, predicted),
        "curves": threshold_curves(truth, scores, steps=21),
        "calibration": calibration_bins(truth, scores),
    }


def train_one(name, splits, output_dir, epochs, batch_size, learning_rate, device):
    training = DataLoader(WaterDataset(splits["training"], augment=True), batch_size=batch_size, shuffle=True)
    validation = DataLoader(WaterDataset(splits["validation"]), batch_size=batch_size)
    test = DataLoader(WaterDataset(splits["test"]), batch_size=batch_size)
    model = make_model(name).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    criterion = MaskedBCEDice()
    history, best_loss, best_state = [], float("inf"), None
    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []
        for image, target, valid in training:
            image, target, valid = image.to(device), target.to(device), valid.to(device).bool()
            optimizer.zero_grad()
            loss = criterion(model(image), target, valid)
            loss.backward()
            optimizer.step()
            train_losses.append(float(loss))
        validation_result = evaluate(model, validation, device)
        history.append({"epoch": epoch, "training_loss": round(float(np.mean(train_losses)), 6), "validation_loss": validation_result["loss"]})
        if validation_result["loss"] < best_loss:
            best_loss = validation_result["loss"]
            best_state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
        print(f"{name} epoch {epoch}/{epochs}: train={history[-1]['training_loss']} val={validation_result['loss']}", flush=True)
    model.load_state_dict(best_state)
    filename = {"unet": "unet.pt", "deeplabv3plus": "deeplabv3plus.pt", "segformer": "segformer.pt"}[name]
    torch.save({"model": name, "bands": BANDS, "state_dict": best_state}, output_dir / filename)
    return {"history": history, "test": evaluate(model, test, device), "weight_file": str(output_dir / filename)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=["unet"])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    pairs = find_pairs(args.data_root)
    splits = split_by_event(pairs, args.seed)
    output_dir = Path(__file__).parent / "model_weights"
    experiment_dir = Path(__file__).parent / "experiments"
    output_dir.mkdir(exist_ok=True)
    experiment_dir.mkdir(exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    report_path = experiment_dir / "latest.json"
    report = {
        "dataset": "Sen1Floods11 v1.1 hand-labelled Sentinel-2",
        "dataset_source": "gs://sen1floods11/v1.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "device": str(device),
        "split_strategy": "geographic event-level 70/15/15",
        "samples": {key: len(value) for key, value in splits.items()},
        "models": {},
    }
    if report_path.is_file():
        try:
            previous = json.loads(report_path.read_text(encoding="utf-8"))
            if previous.get("dataset") == report["dataset"] and previous.get("split_strategy") == report["split_strategy"]:
                report["models"].update(previous.get("models", {}))
        except (OSError, json.JSONDecodeError):
            pass
    for name in args.models:
        report["models"][name] = train_one(name, splits, output_dir, args.epochs, args.batch_size, args.learning_rate, device)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
