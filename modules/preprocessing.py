import albumentations as A
from albumentations.pytorch import ToTensorV2

infer_tf = A.Compose([
    A.Resize(256, 256),
    A.Normalize((0.485,0.456,0.406),(0.229,0.224,0.225)),
    ToTensorV2()
])

def preprocess(image_np):
    aug = infer_tf(image=image_np)
    return aug["image"]
