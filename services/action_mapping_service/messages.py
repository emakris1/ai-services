from typing import Literal

Actor = Literal["Actor.driver", "Actor.gunner"]
Action = str
Phrase = str

ActionPhraseMap = dict[Action, list[Phrase]]
ActionMapping = dict[Actor, ActionPhraseMap]
