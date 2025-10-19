import random
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from transformers import AutoModel, AutoTokenizer, PreTrainedModel
from transformers.modeling_outputs import BaseModelOutputWithPooling, ModelOutput

from .retriever_config import RetrieverConfig


@dataclass
class ContrastiveTrainingModelOutput(ModelOutput):
    r_at_1: Optional[Tensor] = None


@dataclass
class RetrieverModelOutput(ContrastiveTrainingModelOutput):
    loss: Optional[torch.Tensor] = None
    query_features: Optional[torch.Tensor] = None
    query_last_hidden_state: Optional[torch.Tensor] = None
    passage_features: Optional[torch.Tensor] = None
    passage_last_hidden_state: Optional[torch.Tensor] = None


def unpad_tensor(tensors, mask, op=nn.Identity(), skip_first=False):
    # Assuming tensors is a batched tensor of shape (N, ...)
    mask = mask.bool()
    start = 1 if skip_first else 0
    return torch.stack([op(tensors[i, mask[i]][start:]) for i in range(len(tensors))])


def pool_bert_output(
    pooling_strategy,
    outputs: BaseModelOutputWithPooling,
    attention_mask: Optional[torch.Tensor] = None,
):
    if pooling_strategy == "cls_tanh":
        pooler_output = outputs.pooler_output
    elif pooling_strategy == "cls":
        pooler_output = outputs.last_hidden_state[:, 0]
    elif pooling_strategy == "mean":
        pooler_output = outputs.last_hidden_state[:, 1:] * attention_mask[:, 1:, None]
        pooler_output = pooler_output.sum(dim=1) / attention_mask[:, 1:].sum(dim=1, keepdim=True)
    elif pooling_strategy == "l2norm_sum":
        op = lambda x: F.normalize(x, p=2, dim=-1).sum(dim=0)
        pooler_output = unpad_tensor(outputs.last_hidden_state, attention_mask, op=op, skip_first=True)
    else:
        raise ValueError(f"Invalid pooling strategy: {pooling_strategy}")

    outputs["pooler_output"] = pooler_output


class RetrieverModel(PreTrainedModel):
    config_class = RetrieverConfig

    def __init__(
        self,
        config: RetrieverConfig,
        embedding_model: Optional[PreTrainedModel] = None,
    ):
        super().__init__(config)
        self.embedding_model = embedding_model or AutoModel.from_config(config.embedding_config)

        if config.logit_scale_init_value is None:
            self.register_buffer("logit_scale", torch.tensor([0.0]))
        else:
            self.logit_scale = nn.Parameter(torch.tensor(config.logit_scale_init_value))

        self.tokenizer = getattr(self.embedding_model, "tokenizer", None)


    def init_tokenizer(self):
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.embedding_config.name_or_path
            )

    
    def set_pooling_strategy(self, ps: str):
        self.config.pooling_strategy = ps


    @property
    def pooling_strategy(self):
        return self.config.pooling_strategy


    def get_logit_scale(self):
        return self.logit_scale.exp()


    def embedding_model_forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs,
    ) -> BaseModelOutputWithPooling:
        return self.embedding_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **kwargs,
        )
    

    def get_embeddings(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs,
    ) -> torch.Tensor:
        outputs = self.embedding_model_forward(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **kwargs,
        )
        pool_bert_output(self.pooling_strategy, outputs, attention_mask)
        return outputs.pooler_output


    def forward(
        self,
        query_input_ids: Optional[torch.Tensor] = None,
        query_attention_mask: Optional[torch.Tensor] = None,
        passage_input_ids: Optional[torch.Tensor] = None,
        passage_attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        embedding_model_kwargs: Optional[dict] = None,
        **kwargs,
    ) -> RetrieverModelOutput:
        embedding_model_kwargs = embedding_model_kwargs or {}

        query_features = self.get_embeddings(
            input_ids=query_input_ids,
            attention_mask=query_attention_mask,
            **embedding_model_kwargs,
        )
        passage_features = self.get_embeddings(
            input_ids=passage_input_ids,
            attention_mask=passage_attention_mask,
            **embedding_model_kwargs,
        )

        query_features = F.normalize(query_features, p=2, dim=-1)
        passage_features = F.normalize(passage_features, p=2, dim=-1)

        logit_scale = self.get_logit_scale()
        q_logits = (query_features @ passage_features.T) * logit_scale
        loss_fn = nn.CrossEntropyLoss()

        if self.config.contrastive_topk:
            pidxs = torch.arange(
                query_features.size(0),
                device=query_features.device,
                dtype=torch.long,
            )[:, None]

            if self.config.sample_contrastive_topk == "sample":
                sampled = random.sample(
                    range(q_logits.shape[-1]), self.config.contrastive_topk
                )
                nidxs = q_logits.argsort(dim=1, descending=True)[:, sampled]
            else:
                nidxs = q_logits.argsort(dim=1, descending=True)[:, :self.config.contrastive_topk]

            idxs = torch.cat([pidxs, nidxs], dim=1)
            q_logits = q_logits.gather(dim=1, index=idxs)

            labels = torch.zeros(
                (query_features.size(0), q_logits.size(1)),
                device=query_features.device,
                dtype=query_features.dtype,
            )
            duplicate_mask = pidxs == idxs
            labels[duplicate_mask] = 1
            labels /= duplicate_mask.sum(dim=1, keepdim=True)

        loss = loss_fn(q_logits, labels)

        preds = q_logits.argmax(dim=-1)
        r_at_1 = torch.stack(
            [labels[i, p] > 0 for i, p in enumerate(preds)]
        ).to(torch.float32).mean().item()

        return RetrieverModelOutput(
            loss=loss,
            query_features=query_features,
            passage_features=passage_features,
            r_at_1=r_at_1,
        )