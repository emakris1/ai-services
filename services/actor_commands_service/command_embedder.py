import messages as m
from sentence_transformers import SentenceTransformer
import numpy as np

Embedding = np.ndarray # 1 dimensional vector
ActionEmbeddings = dict[m.Action, np.ndarray[Embedding]]
EmbeddingTable = dict[m.Actor, ActionEmbeddings]

class CommandEmbedder:
    _embedding_map: dict[str, Embedding] = {}
    _table: EmbeddingTable = {}

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)

    def _init_embedding_map(self, config: m.CommandConfig):
        # This is used because it's a lot faster to forward pass all the sentences 
        # at once instead of doing it individually. Usually ran when the config is
        # first sent.
        phrases = []

        for ac in config.commands:
            for command in ac.commands:
                for phrase in command.phrases:
                    phrases.append(phrase)

        embeddings = self._model.encode(phrases)

        for i in range(len(phrases)):
            self._embedding_map[phrases[i]] = embeddings[i]
                    
    def _embed_sentence(self, sentence: str, cache_embedding=False) -> Embedding:
        if sentence in self._embedding_map:
            return self._embedding_map[sentence]
        
        embedding = self._model.encode(sentence)

        if cache_embedding:
            self._embedding_map[sentence] = embedding

        return embedding

    def match_phrase_to_action(self, language: str, phrase: str, actor: m.Actor) -> tuple[m.Action, float]:
        # TODO: add better support for multiple languages
        if language != 'en' or actor not in self._table:
            return m.Action.UNKNOWN, 0.0

        query_embedding = self._embed_sentence(phrase, cache_embedding=False)

        action_scores: list[tuple[m.Action, float]] = []

        for action in self._table[actor]:
            action_embeddings = self._table[actor][action]

            # Compute cosine similarity to find the multi dimensional distance between
            # the phrase vector and the action phrase vectors.
            similarities = np.dot(action_embeddings, query_embedding) / (
                np.linalg.norm(action_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )

            # Use top k method to filter out outlier similarity scores in calculating
            # overall score.
            top_k = min(3, len(similarities))
            top_sim = sorted(similarities, reverse=True)[:top_k]
            score = np.mean(top_sim)

            action_scores.append((action, score.item()))

        best_action = max(action_scores, key=lambda x: x[1])
        return best_action

    def update_config(self, config: m.CommandConfig):
        if not self._embedding_map:
            self._init_embedding_map(config)

        for ac in config.commands:
            if ac.actor not in self._table:
                self._table[ac.actor] = {}

            for command in ac.commands:
                if command.action not in self._table[ac.actor]:
                    self._table[ac.actor][command.action] = []
                
                for phrase in command.phrases:
                    self._table[ac.actor][command.action].append(self._embed_sentence(phrase)) 
