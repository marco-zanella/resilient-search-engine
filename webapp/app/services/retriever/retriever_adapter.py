import torch
import torch.nn.functional as F

from .retriever_model import RetrieverModel

class SentenceTransformerAdapter:
    def __init__(self, model_name_or_path, device='cpu'):
        self.device = device
        self.model = RetrieverModel.from_pretrained(model_name_or_path, device_map=device)
        self.model.init_tokenizer()
        self.model.eval()
        self.tokenizer = self.model.tokenizer

    def encode(self, texts, normalize=True):
        if isinstance(texts, str):
            texts = [texts]
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors='pt', max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.inference_mode():
            embeddings = self.model.get_embeddings(**inputs)
        if normalize:
            embeddings = F.normalize(embeddings, p=2, dim=-1)
        return embeddings.cpu().numpy()[0]