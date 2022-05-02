import datetime
import math

import numpy

import env
from bot import Bot
from browser import Browser
from browser_mock import BrowserMock


def run():
    cnt = 1
    browser_real = Browser(chromedriver_path=env.CHROMEDRIVER_PATH, headless=False)
    browser_mock = BrowserMock()
    name = f'alpoptile-bot'
    browser_real.setup(name)
    browser_mock.setup(name)
    generation = None
    x_tile_cnt = 8
    y_tile_cnt = 15
    bot = Bot(x_tile_cnt * y_tile_cnt, x_tile_cnt * y_tile_cnt)

    scores = []
    while True:
        real = cnt % 10000 == 0
        need_update = cnt % 100 == 0
        if need_update:
            print(f'평균: {numpy.mean(scores)}')

        if real:
            browser = browser_real
        else:
            browser = browser_mock

        browser.set_canvas()
        prev_score = 0

        generation = 1 if generation is None else generation + 1
        turn = 0
        while True:
            turn += 1
            white_click_cnt = 0
            state = browser.get_canvas_state(turn)
            while True:
                action = bot.act(state)
                value = action.tolist()
                i = value % 8
                j = int(value / 8)
                if state[j * 8 + i] != 0:
                    break
                else:
                    white_click_cnt += 1
                    bot.append_sample(state, action, -1)
            is_gameover, current_score, canvas = browser.play_turn(int(i), int(j))

            """
            보상함수
            """
            reward = 0
            # 기본 제공 점수
            reward += current_score - prev_score

            # 높이 분산값
            heights = []
            for i in range(8):
                for j in range(15):
                    if canvas[j][i] != 0:
                        max_height = 15 - j
                        heights.append(max_height)
                        break
            if len(heights) == 0:
                # get_canvas_state 함수에서 new row를 추가해주지 못하는 버그가 있음
                continue

            mean_height = numpy.mean(heights)
            variance = numpy.mean([(mean_height - height) ** 2 for height in heights])
            reward -= variance

            # 8개씩 추가되는데, 8개 이상 지우지 못하면 안좋다는 것을 알려줌
            # removed_block_cnt = reward ** 0.5
            # reward += removed_block_cnt - 8

            # 턴을 지속할수록 좋다는것을 알려줌
            # reward += turn * 0.5

            if real:
                print(f'[{generation}] [{current_score}] white: {white_click_cnt} ({i}, {j}) {reward}')
            prev_score = current_score

            if is_gameover:
                reward = -100

            bot.append_sample(state, action, reward)
            if is_gameover:
                # 엄청난 패널티 주고 다시 시작
                # print('[gen: %s] [turn: %s] %s' % (generation, turn, prev_score))
                break

        # 재시작
        scores.append(current_score)
        cnt += 1
        if need_update:
            scores = []
            bot.update()
            if real:
                bot.save_model(f"./models/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S.model')}")
        browser.retry()


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        raise e
