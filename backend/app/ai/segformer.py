"""
SegFormer-style lightweight transformer scaffold for water segmentation.

Install PyTorch before using this model for training or inference.
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

    class PatchEncoder(nn.Module):
        def __init__(self, in_channels: int, embed_dim: int):
            super().__init__()
            # A 16 px patch produces 1,024 tokens for a 512 px chip. The former
            # 4 px patch produced 16,384 tokens and exhausted CPU Docker memory
            # because self-attention grows quadratically with token count.
            self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=16, stride=16)
            self.norm = nn.BatchNorm2d(embed_dim)

        def forward(self, x):
            return self.norm(self.proj(x))


    class SegFormerLite(nn.Module):
        def __init__(self, in_channels: int = 6, classes: int = 1, embed_dim: int = 64):
            super().__init__()
            self.patch = PatchEncoder(in_channels, embed_dim)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=embed_dim,
                nhead=4,
                dim_feedforward=embed_dim * 4,
                batch_first=True,
            )
            self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)
            self.head = nn.Sequential(
                nn.Conv2d(embed_dim, 32, 3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, classes, 1),
                nn.Sigmoid(),
            )

        def forward(self, x):
            patches = self.patch(x)
            batch, channels, height, width = patches.shape
            tokens = patches.flatten(2).transpose(1, 2)
            encoded = self.transformer(tokens).transpose(1, 2).reshape(batch, channels, height, width)
            mask = self.head(encoded)
            return torch.nn.functional.interpolate(mask, size=x.shape[-2:], mode="bilinear", align_corners=False)

else:

    class SegFormerLite:  # pragma: no cover
        def __init__(self, *_, **__):
            raise RuntimeError("Install torch to use SegFormerLite.")
