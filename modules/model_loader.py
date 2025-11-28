import os
import torch
import segmentation_models_pytorch as smp
import torch.nn as nn

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

MODEL_PATH = r"C:\Users\Naga Sai\OneDrive\文档\Projects\AIvision_Extract\best_model.pth"

def build_model(device=DEVICE):
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    )

    model.segmentation_head = nn.Sequential(
        nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),
        nn.Conv2d(32, 16, 3, padding=1), nn.ReLU(),
        nn.Conv2d(16, 1, 1)
    )

    return model.to(device).eval()

def load_model():
    if not os.path.exists(MODEL_PATH):
        return None

    model = build_model()
    state = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state)
    model.eval()
    return model
