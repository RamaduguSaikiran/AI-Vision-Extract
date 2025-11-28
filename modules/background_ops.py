import numpy as np
import cv2
from PIL import Image
import torch

from modules.model_loader import DEVICE, load_model
from modules.preprocessing import preprocess

model = load_model()

def uniform_resize(img, size=450):
    # Keeps aspect ratio but fits inside a square box
    img.thumbnail((size, size), Image.Resampling.LANCZOS)

    # Create a black background box
    box = Image.new("RGB", (size, size), (255, 255, 255)) 
    
    # Center the resized image
    x = (size - img.width) // 2
    y = (size - img.height) // 2
    box.paste(img, (x, y))
    return box
def get_mask(image_np):
    if model is None:
        return np.ones(image_np.shape[:2], dtype=np.uint8)

    H, W = image_np.shape[:2]
    tensor = preprocess(image_np).unsqueeze(0).float().to(DEVICE)

    with torch.no_grad():
        pred = torch.sigmoid(model(tensor))[0,0].cpu().numpy()

    mask = (pred > 0.5).astype(np.uint8)
    return cv2.resize(mask, (W, H))

def remove_background(pil_img):
    img_np = np.array(pil_img.convert("RGB"))
    mask = get_mask(img_np)

    # Apply mask
    removed = (img_np * mask[..., None]).astype("uint8")

    # Convert black pixels → transparent
    out = Image.fromarray(removed).convert("RGBA")
    datas = out.getdata()
    new_data = []

    for item in datas:
        # detect black background
        if item[0] < 15 and item[1] < 15 and item[2] < 15:  
            new_data.append((0, 0, 0, 0))  # transparent
        else:
            new_data.append(item)

    out.putdata(new_data)
    return out, mask


def blur_background(pil_img, blur_value=45):
    img_np = np.array(pil_img)
    removed, mask = remove_background(pil_img)

    # Kernel must be odd — ensure blur_value is odd
    k = blur_value if blur_value % 2 == 1 else blur_value + 1

    blurred = cv2.GaussianBlur(img_np, (k, k), 0)
    result = img_np * mask[...,None] + blurred * (1-mask[...,None])
    return Image.fromarray(result)

def replace_background_color(pil_img, hex_color):
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

    img_np = np.array(pil_img)
    mask = get_mask(img_np)

    bg_layer = np.full(img_np.shape, rgb, dtype=np.uint8)
    result = img_np * mask[...,None] + bg_layer * (1-mask[...,None])

    return Image.fromarray(result)

def replace_background_image(pil_img, bg_image):
    img_np = np.array(pil_img)
    bg = bg_image.resize(pil_img.size)
    bg_np = np.array(bg)

    mask = get_mask(img_np)
    result = img_np * mask[...,None] + bg_np * (1-mask[...,None])

    return Image.fromarray(result)
