import numpy as np
import cv2
from PIL import Image
import torch
import io

from modules.model_loader import load_model
from modules.preprocessing import preprocess


# -------------------------
# LAZY MODEL CACHING
# -------------------------
_cached_model = None
_cached_device = None


def get_model_and_device():
    """
    Load the model only once, on first use.
    """
    global _cached_model, _cached_device

    if _cached_model is None or _cached_device is None:
        try:
            model, device = load_model()
        except Exception as e:
            print("[background_ops] Error loading model:", e)
            model, device = None, torch.device("cpu")

        _cached_model = model
        _cached_device = device

    return _cached_model, _cached_device


# ============ UTIL: Accept PIL or File Path ============

def load_image_auto(img_or_path):
    if isinstance(img_or_path, Image.Image):
        return img_or_path.convert("RGB")
    if isinstance(img_or_path, str):
        return Image.open(img_or_path).convert("RGB")
    raise ValueError("Invalid image input: must be PIL image or file path")


def save_image_if_requested(pil_img, save_to=None):
    if save_to is None:
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return buf.getvalue()
    else:
        pil_img.save(save_to)
        return None


# ============ MODEL MASK ============

def get_mask(image_np):
    model, device = get_model_and_device()

    # If model missing, just return full-foreground mask
    if model is None:
        return np.ones(image_np.shape[:2], dtype=np.uint8)

    H, W = image_np.shape[:2]
    tensor = preprocess(image_np).unsqueeze(0).float().to(device)

    with torch.no_grad():
        pred = torch.sigmoid(model(tensor))[0, 0].cpu().numpy()

    mask = (pred > 0.5).astype(np.uint8)
    return cv2.resize(mask, (W, H))


# ============ BACKGROUND REMOVAL ============

def remove_background(img_or_path, save_to=None):
    pil_img = load_image_auto(img_or_path)
    img_np = np.array(pil_img)

    mask = get_mask(img_np)
    removed = (img_np * mask[..., None]).astype("uint8")

    out = Image.fromarray(removed).convert("RGBA")

    # Remove BLACK pixels → transparent
    datas = out.getdata()
    new_data = []
    for r, g, b, a in datas:
        if (r, g, b) == (0, 0, 0):
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, a))
    out.putdata(new_data)

    return save_image_if_requested(out, save_to)


# ============ BLUR ============

def blur_background(img_or_path, blur_px=45, save_to=None):
    pil_img = load_image_auto(img_or_path)
    img_np = np.array(pil_img)

    mask = get_mask(img_np)

    k = blur_px if blur_px % 2 == 1 else blur_px + 1
    blurred = cv2.GaussianBlur(img_np, (k, k), 0)

    result = img_np * mask[..., None] + blurred * (1 - mask[..., None])
    out = Image.fromarray(result.astype("uint8"))

    return save_image_if_requested(out, save_to)


# ============ COLOR REPLACE ============

def replace_background_color(img_or_path, hex_color, save_to=None):
    pil_img = load_image_auto(img_or_path)
    img_np = np.array(pil_img)

    # hex_color: "#rrggbb"
    rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    mask = get_mask(img_np)

    bg_layer = np.full(img_np.shape, rgb, dtype=np.uint8)
    result = img_np * mask[..., None] + bg_layer * (1 - mask[..., None])

    out = Image.fromarray(result.astype("uint8"))
    return save_image_if_requested(out, save_to)


# ============ IMAGE REPLACE ============

def replace_background_image(img_or_path, bg_or_path, save_to=None):
    pil_img = load_image_auto(img_or_path)
    bg_img = load_image_auto(bg_or_path)

    bg_img = bg_img.resize(pil_img.size)
    img_np = np.array(pil_img)
    bg_np = np.array(bg_img)

    mask = get_mask(img_np)
    result = img_np * mask[..., None] + bg_np * (1 - mask[..., None])

    out = Image.fromarray(result.astype("uint8"))
    return save_image_if_requested(out, save_to)


# ============ UNIFORM RESIZE FOR GALLERY & BATCH ============

def uniform_resize(pil_img, size=450):
    img = pil_img.copy()
    img.thumbnail((size, size), Image.Resampling.LANCZOS)

    box = Image.new("RGB", (size, size), (255, 255, 255))
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    box.paste(img, (x, y))
    return box
