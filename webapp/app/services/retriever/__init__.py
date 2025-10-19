from .retriever_config import RetrieverConfig
from .retriever_model import RetrieverModel, RetrieverModelOutput, pool_bert_output
from .retriever_adapter import SentenceTransformerAdapter
from transformers import AutoConfig, AutoModel

AutoConfig.register("retriever", RetrieverConfig)
AutoModel.register(RetrieverConfig, RetrieverModel)