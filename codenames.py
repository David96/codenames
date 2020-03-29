import random
from enum import Enum

WIDTH = 5
HEIGHT = 5

WHITE = 0
RED = 1
BLUE = 2
BLACK = 3

REASON_BLACK = 1
REASON_ALL_OPEN = 2

class Player:

    def __init__(self, name, colour, gamemaster):
        self.name = name
        self.colour = colour
        self.gamemaster = gamemaster

class CodeNames:

    def __init__(self):
        self.state = []
        self.colours = []
        self.words = []
        self.players = {}
        self.blue_left = 0
        self.red_left = 0
        self.winner = -1
        self.reason = -1

    def _generate_random_state(self, red_begins):
        colour_counts = {}
        colour_counts[WHITE] = 7
        self.blue_left = colour_counts[BLUE] = 8 if red_begins else 9
        self.red_left = colour_counts[RED] = 9 if red_begins else 8
        colour_counts[BLACK] = 1
        self.state = []
        self.colours = []
        assert sum(colour_counts.values()) == WIDTH*HEIGHT
        for i in range(WIDTH*HEIGHT):
            self.state.append({
                    'word': self.words[i],
                  'colour': -1,
                  'opened': False})
            self.colours.append(random.sample(colour_counts[WHITE] * [WHITE] +
                                               colour_counts[BLUE] * [BLUE]  +
                                                colour_counts[RED] * [RED]   +
                                              colour_counts[BLACK] * [BLACK], 1)[0])
            colour_counts[self.colours[-1]] -= 1

    def reset(self, words, red_begins=True):
        assert len(words) == WIDTH*HEIGHT
        for player in self.players.values():
            player.gamemaster = False
        self.winner = self.reason = -1
        self.words = words
        self._generate_random_state(red_begins)

    def add_player(self, name, colour=-1, gamemaster=False):
        self.players[name] = Player(name, colour, gamemaster)

    def gamemaster_count(self):
        return len([player for player in self.players.values() if player.gamemaster])

    def check_gameover(self, index, name):
        if self.colours[index] == BLACK:
            self.winner = RED if self.players[name].colour == BLUE else BLUE
            self.reason = REASON_BLACK
        elif self.blue_left == 0:
            self.winner = BLUE
            self.reason = REASON_ALL_OPEN
        elif self.red_left == 0:
            self.winner = RED
            self.reason = REASON_ALL_OPEN

    def open_field(self, index, username):
        self.state[index]['colour'] = self.colours[index]
        if self.colours[index] == BLUE:
            self.blue_left -= 1
        elif self.colours[index] == RED:
            self.red_left -= 1
        self.check_gameover(index, username)
        return self.colours[index]
