from codenames.board import CardTypes
from .constants import RED_TEAM


class Team:
    def __init__(self, name, game, emoji):
        self.spymaster = None  # Player.name
        self.name = name  # Blue or red
        self.game = game
        self.emoji = emoji
        self.card_type = CardTypes.Red if name == RED_TEAM else CardTypes.Blue
        self.guesses = None

    # Returns the players on this team
    def get_players(self):
        return list(filter(lambda x: x[1].team == self, self.game.players.items()))
