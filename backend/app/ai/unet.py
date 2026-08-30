try:
    import torch
    import torch.nn as nn
except Exception:  # PyTorch is optional for lightweight demo deployment.
    torch = None
    nn = None


if nn:
    class DoubleConv(nn.Module):
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
            )

        def forward(self, x):
            return self.net(x)


    class UNet(nn.Module):
        def __init__(self, in_channels: int = 3, out_channels: int = 1):
            super().__init__()
            self.down1 = DoubleConv(in_channels, 32)
            self.pool1 = nn.MaxPool2d(2)
            self.down2 = DoubleConv(32, 64)
            self.pool2 = nn.MaxPool2d(2)
            self.bridge = DoubleConv(64, 128)
            self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
            self.conv2 = DoubleConv(128, 64)
            self.up1 = nn.ConvTranspose2d(64, 32, 2, stride=2)
            self.conv1 = DoubleConv(64, 32)
            self.out = nn.Conv2d(32, out_channels, 1)

        def forward(self, x):
            d1 = self.down1(x)
            d2 = self.down2(self.pool1(d1))
            bridge = self.bridge(self.pool2(d2))
            u2 = self.up2(bridge)
            c2 = self.conv2(torch.cat([u2, d2], dim=1))
            u1 = self.up1(c2)
            c1 = self.conv1(torch.cat([u1, d1], dim=1))
            return torch.sigmoid(self.out(c1))
else:
    UNet = None

