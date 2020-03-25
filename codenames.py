import random
from enum import Enum

WIDTH = 5
HEIGHT = 5

WHITE = 0
RED = 1
BLUE = 2
BLACK = 3

class CodeNames:

    def __init__(self, words):
        self.state = []
        self.colours = []
        self.reset(words)

    def _generate_random_state(self):
        colour_counts = {}
        colour_counts[WHITE] = 7
        # TODO: take turns
        colour_counts[BLUE] = 8
        colour_counts[RED] = 9
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

    def reset(self, words):
        assert len(words) == WIDTH*HEIGHT
        self.words = words
        self._generate_random_state()

    def _get_field_of_list(self, l, x, y):
        return l[y*WIDTH + x]

    def _set_field_of_list(self, l, x, y, v):
        l[y*WIDTH + x] = v

    def get_field(self, x, y):
        return self._get_field_of_list(self.state, x, y)

    def set_field(self, x, y, value):
        self._set_field_of_list(self.state, x, y, value)

    def get_word(self, x, y):
        return self._get_field_of_list(self.words, x, y)

    def open_field(self, index):
        self.state[index]['colour'] = self.colours[index]
        return self.colours[index]
