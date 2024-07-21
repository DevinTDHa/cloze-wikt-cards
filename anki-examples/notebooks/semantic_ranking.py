from typing import List
import torch
import numpy as np
from sentence_transformers import SentenceTransformer


def format_translation(source, target):
    # Format according to XLIFF
    return f"query: <source>{source}</source><target>{target}</target>"


def format_example(ex):
    # Use "query: " prefix for symmetric tasks such as semantic similarity, bitext mining, paraphrase retrieval.
    return f"query: {ex}"


class SimilarityRanker:
    """
    Class for ranking examples based on their similarity to a given query.

    Args:
        model_name (str): The name of the pre-trained model to use for encoding the texts.
        batch_size (int): The batch size to use for encoding the texts.
        device (str): The device to use for encoding the texts.

    Attributes:
        model (SentenceTransformer): The SentenceTransformer model used for encoding the texts.
        batch_size (int): The batch size used for encoding the texts.
        device (str): The device used for encoding the texts.
    """

    def __init__(
        self,
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        batch_size=32,
        device="cuda",
    ):
        self.model: SentenceTransformer = SentenceTransformer(model_name).to("cuda")
        self.batch_size = batch_size
        self.device = device

    def encode(self, texts):
        """
        Encode a list of texts into their corresponding embeddings.

        Args:
            texts (List[str]): The list of texts to encode.

        Returns:
            torch.Tensor: The encoded embeddings.
        """
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_tensor=True,
            device=self.device,
            convert_to_numpy=False,
            normalize_embeddings=True,
        )

    def sort(self, vi: str, examples: List[str], key=lambda x: x):
        """
        Sort a list of examples based on their similarity to a given query.

        Args:
            vi (str): The query text.
            examples (List[str]): The list of examples to sort.
            key (function): The key function to apply to each example before computing similarity.

        Returns:
            np.ndarray: The sorted examples.
        """
        all_enc = self.encode([vi] + [key(ex) for ex in examples])
        query_enc, examples_enc = all_enc[0], all_enc[1:]
        similarities = torch.cosine_similarity(query_enc[None], examples_enc, dim=1)
        sorted_indices = (
            torch.argsort(similarities, descending=True).cpu().detach().numpy()
        )
        return np.array(examples)[sorted_indices]
