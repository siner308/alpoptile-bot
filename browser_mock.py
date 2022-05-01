import datetime
import math
import random


class BrowserMock:
    driver = None
    name = None
    turn = None
    canvas = None
    canvas_width = None
    canvas_height = None
    tile_width = None
    tile_height = None
    timestamp = None

    def setup(self, player_name):
        self.name = player_name
        self.score = 0
        self.timestamp = datetime.datetime.now().timestamp()

    def set_canvas(self):
        self.canvas = [[0 for i in range(8)] for j in range(15)]

    def is_gameover(self):
        for x in self.canvas[0]:
            if x != 0:
                return True
        return False

    def get_canvas_state(self, turn):
        if self.name is None:
            print('not initialized error')
            raise ValueError

        for j in range(1, 15, 1):
            self.canvas[j - 1] = self.canvas[j]

        self.canvas[-1] = self.generate_new_row()
        if math.isnan(self.canvas[0][0]):
            print('nan is detected')
        return [cell for row in self.canvas for cell in row]

    def generate_new_row(self):
        return [random.randrange(1, 4, 1) for i in range(8)]

    def play_turn(self, i, j):
        # 클릭해서 타일없애주고 스코어처리
        target_color = self.canvas[j][i]
        reward = self.click(i, j, target_color=target_color)
        self.score += reward ** 2

        for j in range(15):
            for i in range(8):
                if self.canvas[j][i] == -1:
                    self.canvas[j][i] = 0

        while True:
            breakable = True
            for j in range(14):
                for i in range(8):
                    if self.canvas[j][i] != 0 and self.canvas[j + 1][i] == 0:
                        self.canvas[j][i], self.canvas[j + 1][i] = self.canvas[j + 1][i], self.canvas[j][i]
                        breakable = False

            if breakable:
                break

        if self.is_gameover():
            return True, self.score

        return False, self.score

    def retry(self):
        self.turn = 0
        self.timestamp = datetime.datetime.now().timestamp()
        self.score = 0

    def click(self, i, j, target_color):
        if i >= 8 or i < 0 or j >= 15 or j < 0:
            return 0
        if self.canvas[j][i] != target_color:
            return 0

        self.canvas[j][i] = -1
        reward = 1

        reward += self.click(i + 1, j, target_color)
        reward += self.click(i - 1, j, target_color)
        reward += self.click(i, j + 1, target_color)
        reward += self.click(i, j - 1, target_color)
        return reward
