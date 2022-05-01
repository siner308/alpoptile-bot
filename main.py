import math

import env
from bot import Bot
from browser import Browser
from browser_mock import BrowserMock


def run():
    browser_real = Browser(chromedriver_path=env.CHROMEDRIVER_PATH, headless=False)
    browser_mock = BrowserMock()
    name = f'alpoptile-bot'
    browser_real.setup(name)
    browser_mock.setup(name)
    generation = None
    x_tile_cnt = 8
    y_tile_cnt = 15
    bot = Bot(x_tile_cnt * y_tile_cnt, x_tile_cnt * y_tile_cnt, './models/20220501_014831.model')

    while True:
        real = cnt % 1000 == 0
        if real:
            browser = browser_real
        else:
            browser = browser_mock

        browser.set_canvas()
        prev_score = 0

        generation = 1 if generation is None else generation + 1

        while True:
            state = browser.get_canvas_state()
            while True:
                action = bot.act(state)
                value = action.tolist()
                i = value % 8
                j = int(value / 8)
                if state[j * 8 + i] != 0:
                    break
            is_gameover, current_score = browser.play_turn(int(i), int(j))
            reward = current_score - prev_score
            print(f'[{current_score}] ({i}, {j}) +{reward}')
            prev_score = current_score

            if is_gameover:
                reward = -9999

            bot.append_sample(state, action, reward)

            if is_gameover:
                # 엄청난 패널티 주고 다시 시작
                print(current_score)
                break

        # 재시작
        bot.update()
        browser.retry()


if __name__ == '__main__':
    run()
