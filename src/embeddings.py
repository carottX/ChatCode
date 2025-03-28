from langchain_huggingface import HuggingFaceEmbeddings
from constants import EmbeddingsModel
import sentence_transformers


class Embeddings:
    def __init__(
        self
    ):
        """
        Initializes the Embeddings class with the specified model and deployment.
        """
        self.embeddings = HuggingFaceEmbeddings(
            # model_name = 'intfloat/multilingual-e5-large-instruct'
            model_name = 'codesage/codesage-small',
            model_kwargs={
           "trust_remote_code": True
            },
        )