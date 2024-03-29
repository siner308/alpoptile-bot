import datetime
import time

import numpy

import env
from bot import Bot
from browser import Browser
from browser_mock import BrowserMock


def run():
    cnt = 1
    agent_cnt = 100
    bot_path = None
    # bot_path = './models/20220506_001509.model'
    # browser_real = Browser(chromedriver_path=env.CHROMEDRIVER_PATH, headless=False)
    name = f'alpoptile-bot'
    # browser_real.setup(name)
    x_tile_cnt = 8
    y_tile_cnt = 15
    browsers = [BrowserMock() for _ in range(agent_cnt)]

    while True:
        agents = [Bot(x_tile_cnt * y_tile_cnt * 4, x_tile_cnt * y_tile_cnt, bot_path) for _ in range(agent_cnt)]

        total_scores = []
        min_scores = []
        max_scores = []
        avg_scores = []
        for i, browser, agent in zip(range(agent_cnt), browsers, agents):
            min_score, max_score, avg_score = train(browser, agent, is_training=True)
            # total_score = (min_score * 5) + (max_score / 5) + avg_score
            total_score = min_score
            # print(f'[{i}] min: {min_score} avg: {avg_score} max: {max_score} total: {total_score}')
            # print(f'[{i}] {min_score}')
            total_scores.append(total_score)
            min_scores.append(min_score)
            avg_scores.append(avg_score)
            max_scores.append(max_score)

        next_gen = max(total_scores)
        next_gen_idx = total_scores.index(next_gen)
        print(f'[{cnt}th gen] [{next_gen_idx}] min: {min_scores[next_gen_idx]} avg: {avg_scores[next_gen_idx]} max: {max_scores[next_gen_idx]} is next generation')

        next_bot = agents[next_gen_idx]
        bot_path = f"./models/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S.model')}"
        next_bot.save_model(bot_path)
        cnt += 1
        # if cnt % 2 == 0:
        #     train(browser_real, next_bot, is_training=False)


def train(browser: BrowserMock or Browser, bot: Bot, is_training: bool):
    min_score = 99999999
    max_score = 0
    scores = []

    repeat_cnt = 100 if is_training else 1

    for gen in range(repeat_cnt):
        browser.set_canvas()
        turn = 0
        prev_score = 0

        while True:
            turn += 1
            white_click_cnt = 0
            canvas = browser.get_canvas_state(turn)

            def parse_color(color):
                if color == 1:
                    return [1, 0, 0, 0]
                if color == 2:
                    return [0, 1, 0, 0]
                if color == 3:
                    return [0, 0, 1, 0]
                return [0, 0, 0, 1]
            state = [color for row in canvas for cell in row for color in parse_color(cell)]

            while True:
                action = bot.act(state)
                value = action.tolist()
                i = value % 8
                j = int(value / 8)
                if canvas[j][i] != 0:
                    break
                else:
                    if is_training:
                        white_click_cnt += 1
                        bot.append_sample(state, action, -1)
                    continue

            is_gameover, current_score, canvas = browser.play_turn(int(i), int(j))

            """
            보상함수
            """
            reward = 0
            # 기본 제공 점수
            removed_block_cnt = (current_score - prev_score) ** 0.5
            reward += removed_block_cnt ** 2

            # 높이 분산값
            heights = []
            for _i in range(8):
                for _j in range(15):
                    if canvas[_j][_i] != 0:
                        max_height = 15 - _j
                        heights.append(max_height)
                        break
            if len(heights) == 0:
                # get_canvas_state 함수에서 new row를 추가해주지 못하는 버그가 있음
                continue

            mean_height = numpy.mean(heights)
            variance = numpy.mean([(mean_height - height) ** 2 for height in heights])
            # total_tile_cnt = sum(heights)
            max_height = max(heights)

            if removed_block_cnt == 1:
                if max_height > 5:
                    reward -= 5

            if mean_height > 8:
                reward -= 5  # 평균높이
                if removed_block_cnt < 8:
                    reward -= 5

            if max_height > 10:
                reward -= 5

            if max_height > 12:
                if variance > 1:
                    reward -= 5  # 분산

            # 8개씩 추가되는데, 8개 이상 지우지 못하면 안좋다는 것을 알려줌

            prev_score = current_score

            if is_gameover:
                reward = -10

            if is_training:
                bot.append_sample(state, action, reward)
            if is_gameover:
                if max_score < current_score:
                    max_score = current_score
                if min_score > current_score:
                    min_score = current_score
                break

        # 재시작
        scores.append(current_score)
        if is_training:
            bot.update()
        browser.retry()

    return min_score, max_score, numpy.mean(scores)


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        raise e
