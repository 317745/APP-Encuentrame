import io
from ultralytics import YOLO
import numpy as np
import cv2
from PIL import Image

model = YOLO("src/models/yolo11m.pt")
def detect_cat(img):
    results = model(img, conf=0.25, classes=[15], save=False)
    boxes = results[0].boxes
    total_cats = len(boxes)

    if total_cats > 1:
            return {
                "msg": "Se requiere maximo un gato por foto.",
                "True": False
                }
    elif total_cats < 1:
        return {
            "msg": "Se requiere minimo un gato por foto.",
            "True": False
            }
    else: 
        return {
            "True": True, 
            "img": img,
            "boxes": boxes
            }

def crop_img(file_bytes: bytes, padding=1.1):
    nparr = np.frombuffer(file_bytes, np.uint8)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    detected_cats = detect_cat(img_cv)
    if not detected_cats["True"]:
        return detected_cats

    boxes = detected_cats["boxes"]

    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    w, h = img_pil.size

    box = boxes.xyxy[0].cpu().numpy() 
    xmin, ymin, xmax, ymax = box

    bw = xmax - xmin
    bh = ymax - ymin

    bw_pad = bw * padding
    bh_pad = bh * padding

    xc = xmin + bw / 2
    yc = ymin + bh / 2
    
    new_xmin = int(xc - bw_pad / 2)
    new_ymin = int(yc - bh_pad / 2)
    new_xmax = int(xc + bw_pad / 2)
    new_ymax = int(yc + bh_pad / 2)

    cropped = img_pil.crop((
        max(0, new_xmin), 
        max(0, new_ymin), 
        min(w, new_xmax), 
        min(h, new_ymax)
    ))

    buffer = io.BytesIO()
    cropped.save(buffer, format="JPEG")
    cropped_bytes = buffer.getvalue()

    return {
        "True": True,
        "cropped_image": cropped_bytes
    }