import re
import string
from transformers import pipeline
from messages import Actor, Action


class ActionCrossEncoder:
    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model='facebook/bart-large-mnli')
        self._warm_up_model()
        self.actions: dict[Actor, dict[str, Action]] = {}

    def add_action(self, actor: Actor, action: Action, label: str):
        if actor not in self.actions:
            self.actions[actor] = {}
        self.actions[actor][label] = action

    def classify(self, actor: Actor, phrase: str, language: str = 'en') -> tuple[Action, float]:
        if language != 'en' or actor not in self.actions:
            return Action.UNKNOWN, -1.0
        phrases = list(self.actions[actor].keys())
        cleaned_phrase = self._clean_text(phrase)
        inference = self.classifier(cleaned_phrase, phrases)
        top_label = inference['labels'][0]
        top_score = inference['scores'][0]
        return self.actions[actor][top_label], top_score

    def __len__(self):
        return sum(len(actions) for actions in self.actions.values())

    def _clean_text(self, text: str) -> str:
        t = text.lower()
        t = t.translate(str.maketrans('', '', string.punctuation))
        t = re.sub(r'\s+', ' ', t)
        return t.strip()

    def _warm_up_model(self):
        # First pass is slow, so do a dummy classification to warm up
        self.classifier("test", ["test"])
