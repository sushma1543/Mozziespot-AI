"""
DeepLabV3+ style segmentation scaffold for waterbody extraction.

This file is intentionally optional: the web app can run without PyTorch, while
research runs can install torch and train/serve the model.
"""

try:
    import torch
    from torch import nn
except Exception:  # pragma: no cover - optional research dependency
    torch = None
    nn = None


def available() -> bool:
    return torch is not None and nn is not None


if available():

    class ASPP(nn.Module):
        def __init__(self, channels: int):
            super().__init__()
            self.branches = nn.ModuleList(
                [
                    nn.Conv2d(channels, channels, 1),
                    nn.Conv2d(channels, channels, 3, padding=6, dilation=6),
                    nn.Conv2d(channels, channels, 3, padding=12, dilation=12),
                    nn.Conv2d(channels, channels, 3, padding=18, dilation=18),
                ]
            )
            self.project = nn.Sequential(nn.Conv2d(channels * 4, channels, 1), nn.ReLU(inplace=True))

        def forward(self, x):
            return self.project(torch.cat([branch(x) for branch in self.branches], dim=1))


    class DeepLabV3PlusLite(nn.Module):
        def __init__(self, in_channels: int = 6, classes: int = 1):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Conv2d(in_channels, 32, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, 64, 3, stride=2, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(64, 128, 3, stride=2, padding=1),
                nn.ReLU(inplace=True),
            )
            self.aspp = ASPP(128)
            self.decoder = nn.Sequential(
                nn.ConvTranspose2d(128, 64, 2, stride=2),
                nn.ReLU(inplace=True),
                nn.ConvTranspose2d(64, 32, 2, stride=2),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, classes, 1),
                nn.Sigmoid(),
            )

        def forward(self, x):
            return self.decoder(self.aspp(self.encoder(x)))

else:

    class DeepLabV3PlusLite:  # pragma: no cover
        def __init__(self, *_, **__):
            raise RuntimeError("Install torch to use DeepLabV3PlusLite.")
