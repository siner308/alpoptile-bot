import datetime
from time import sleep

import env
from bot import Bot
from browser import Browser


def run():
    browser = Browser(chromedriver_path=env.CHROMEDRIVER_PATH)
    name = f'alpoptile-bot'
    browser.setup(name)

    bot = Bot()
    while True:
        browser.set_canvas()
        prev_score = 0
        while True:
            state = browser.get_canvas_state()
            i, j = bot.get_action(state)

            is_gameover, current_score = browser.play_turn(i, j)
            reward = current_score - prev_score
            print(f'[{current_score}] ({i}, {j}) +{reward}')
            prev_score = current_score

            if is_gameover:
                reward = -9999

            bot.update(state, i, j, reward)

            if is_gameover:
                # 엄청난 패널티 주고 다시 시작
                print(current_score)
                break

        # 재시작
        browser.retry()


if __name__ == '__main__':
    run()
