import re
import string

from ai_common.enums.actor_commands import Actor, Action
from ai_common.messages import Command
from transformers import pipeline


class ActionCrossEncoder:
    def __init__(self):
        self.classifier = pipeline(
            "zero-shot-classification",
            model='facebook/bart-large-mnli')
        self._warm_up_model()
        self.actions: dict[Actor, dict[str, tuple[Action, str]]] = {}

    def add_action_reply(self, actor: Actor, command: Command):
        if actor not in self.actions:
            self.actions[actor] = {}
        for label, (action, _) in self.actions[actor].items():
            if command.action == action:
                del self.actions[actor][label]
                break
        self.actions[actor][self._clean_text(command.label)] = (command.action, command.reply)

    def classify(self, actor: Actor, phrase: str, language: str = 'en') -> tuple[tuple[Action, str], float]:
        if language != 'en' or actor not in self.actions:
            return (Action.UNKNOWN, ''), -1.0
        cleaned_labels = [self._clean_text(label) for label in list(self.actions[actor].keys())]
        cleaned_phrase = self._clean_text(phrase)
        inference = self.classifier(cleaned_phrase, cleaned_labels)
        top_label = inference['labels'][0]
        top_score = inference['scores'][0]
        return self.actions[actor][top_label], top_score

    def _warm_up_model(self):
        # First pass is slow, so do a dummy classification to warm up
        self.classifier("test", ["test"])

    def __len__(self):
        return sum(len(actions) for actions in self.actions.values())

    @staticmethod
    def _clean_text(text: str) -> str:
        t = text.lower()
        t = t.translate(str.maketrans('', '', string.punctuation))
        t = re.sub(r'\s+', ' ', t)
        return t.strip()
