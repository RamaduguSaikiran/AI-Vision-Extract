import os

# Only a simple constant here – no torch import at module level
MODEL_PATH = os.path.join("static", "model", "best_model.pth")


def build_model(device):
    """
    Build the U-Net model lazily.
    Heavy imports happen inside this function.
    """
    import segmentation_models_pytorch as smp
    import torch.nn as nn

    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    )

    # Your custom segmentation head
    model.segmentation_head = nn.Sequential(
        nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),
        nn.Conv2d(32, 16, 3, padding=1), nn.ReLU(),
        nn.Conv2d(16, 1, 1)
    )

    return model.to(device).eval()


def load_model():
    """
    Loads weights lazily when called the first time.
    Returns (model, device) or (None, 'cpu') if no model file exists.
    """
    import torch  # heavy import inside function, not at module load

    if not os.path.exists(MODEL_PATH):
        print(f"[model_loader] MODEL_PATH not found: {MODEL_PATH}")
        return None, torch.device("cpu")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[model_loader] Loading model on device: {device}")

    model = build_model(device)
    state = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model, device
