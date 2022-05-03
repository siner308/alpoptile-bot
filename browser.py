import datetime
import pathlib
import time

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from PIL import Image
from time import sleep
from selenium import webdriver


class Browser:
    driver = None
    name = None
    canvas = None
    canvas_element = None
    canvas_width = None
    canvas_height = None
    tile_width = None
    tile_height = None
    timestamp = None

    def __init__(self, chromedriver_path: str, headless: bool):
        self.driver = self._get_driver(chromedriver_path, headless)

    def setup(self, player_name):
        url = 'http://s0af.panty.run/'
        self.driver.get(url)
        self.name = player_name
        self.timestamp = datetime.datetime.now().timestamp()

        # input player name
        self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/input').send_keys(player_name)
        sleep(0.5)

        # disable animation
        # self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/div[1]/button/div').click()
        # sleep(0.5)

        # click Solo Play
        self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/div[2]/a[1]/button').click()
        sleep(0.5)

    def set_canvas(self):
        self.canvas_element = self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/canvas')
        sleep(0.5)

    def _get_driver(self, chromedriver_path: str, headless: bool):
        print('Initialize ChromeDriver Start...')
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("headless")
            chrome_options.add_argument("window-size=1280x900")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("disable-gpu")
            chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(chromedriver_path, chrome_options=chrome_options)
        sleep(5)
        print('Initialize ChromeDriver Complete...')
        return driver

    def is_gameover(self):
        return 'result' in self.driver.current_url

    def get_canvas_state(self, turn):
        if self.name is None:
            print('not initialized error')
            raise ValueError

        path = pathlib.Path(__file__).parent

        filename = path / 'screenshots' / f'{self.name}-{self.timestamp}-{turn}.png'
        filename = str(filename)
        self.save_image(filename=filename)
        return self.get_pixel_grid(filename=filename, x_cnt=8, y_cnt=15)

    def get_pixel_grid(self, filename, x_cnt, y_cnt):
        image = Image.open(filename)

        if not self.canvas_width or not self.canvas_height:
            self.canvas_width, self.canvas_height = image.size
        if not self.tile_width or not self.tile_height:
            self.tile_width, self.tile_height = int(self.canvas_width / x_cnt), int(self.canvas_height / y_cnt)
        pixels = image.load()
        self.canvas = [[self.get_color(pixels, i, j) for i in range(x_cnt)] for j in range(y_cnt)]
        return self.canvas

    def save_image(self, filename):
        self.canvas_element.screenshot(filename)

    def get_color(self, pixels, i, j):
        x = (i + 0.5) * self.tile_width
        y = (j + 0.5) * self.tile_height
        r, g, b, a = pixels[x, y]
        if g > r and g > b:
            return 1
        if r > g and r > b:
            return 2
        if b > r and b > g:
            return 3
        # if r == 0 and g == 255 and b == 161:
        #     return 1  # green
        # elif r == 255 and g == 161 and b == 0:
        #     return 2  # orange
        # elif r == 0 and g == 161 and b == 255:
        #     return 3  # blue
        return 0  # white

    def play_turn(self, i, j):
        ac = ActionChains(self.driver)
        x = (i + 0.5) * self.tile_width
        y = (j + 0.5) * self.tile_height
        ac.move_to_element(self.canvas_element).move_by_offset(-self.canvas_width / 2, -self.canvas_height / 2).move_by_offset(x, y).click().perform()
        time.sleep(1)

        reward = self.click(i, j, target_color=self.canvas[j][i])

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
            score_element = self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/h1')
            score = int(score_element.text)
            return True, score, self.canvas

        score_element = self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/span')
        score = int(score_element.text.split(': ')[1])
        return False, score, self.canvas

    def retry(self):
        self.timestamp = datetime.datetime.now().timestamp()
        self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/a[1]/button').click()
        sleep(0.5)

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
