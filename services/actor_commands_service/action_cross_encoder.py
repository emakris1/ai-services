from transformers import pipeline
from messages import Actor, Action


class ActionCrossEncoder:
    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model='cross-encoder/nli-MiniLM2-L6-H768')
        self.actions: dict[Actor, dict[str, Action]] = {}

    def add_action(self, actor: Actor, action: Action, label: str):
        if actor not in self.actions:
            self.actions[actor] = {}
        self.actions[actor][label] = action

    def classify(self, actor: Actor, phrase: str, language: str = 'en') -> tuple[Action, float]:
        if language != 'en' or actor not in self.actions:
            return Action.UNKNOWN, -1.0
        phrases = list(self.actions[actor].keys())
        inference = self.classifier(phrase, phrases)
        top_label = inference['labels'][0]
        top_score = inference['scores'][0]
        return self.actions[actor][top_label], top_score
