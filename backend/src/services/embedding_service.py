import io
from pathlib import Path
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms

MODEL_PATH = Path("../src/models/reid_model.pth")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

PREPROCESS = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

class EmbeddingsService:
    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self.device = DEVICE
        self.model = self._load_model(model_path)

    def _load_model(self, model_path: Path) -> nn.Module:
        model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, 512)

        checkpoint = torch.load(model_path, map_location=self.device)
        if isinstance(checkpoint, dict):
            state_dict = (
                checkpoint.get("model_state_dict")
                or checkpoint.get("state_dict")
                or checkpoint
            )
        else:
            state_dict = checkpoint

        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        return model

    def get_embedding(self, image_bytes: bytes) -> list[float]:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = PREPROCESS(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.model(tensor)
            embedding = F.normalize(embedding, p=2, dim=1)

        return embedding.squeeze(0).cpu().tolist()


embedding_service = EmbeddingsService()