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
    turn = None
    canvas = None
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
        self.turn = 0
        self.timestamp = datetime.datetime.now().timestamp()

        # input player name
        self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/input').send_keys(player_name)
        sleep(0.5)

        # disable animation
        self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/div[1]/button/div').click()
        sleep(0.5)

        # click Solo Play
        self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/div[2]/a[1]/button').click()
        sleep(0.5)

    def set_canvas(self):
        self.canvas = self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/canvas')

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

    def get_canvas_state(self):
        if self.name is None or self.turn is None:
            print('not initialized error')
            raise ValueError

        path = pathlib.Path(__file__).parent

        filename = path / 'screenshots' / f'{self.name}-{self.timestamp}-{self.turn}.png'
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
        return [self.get_color(pixels, i, j) for j in range(y_cnt) for i in range(x_cnt)]

    def save_image(self, filename):
        self.canvas.screenshot(filename)

    def get_color(self, pixels, i, j):
        x = (i + 0.5) * self.tile_width
        y = (j + 0.5) * self.tile_height
        r, g, b, a = pixels[x, y]
        if r == 0 and g == 255 and b == 161:
            return 1  # green
        elif r == 255 and g == 161 and b == 0:
            return 2  # orange
        elif r == 0 and g == 161 and b == 255:
            return 3  # blue
        return 0  # white

    def play_turn(self, i, j):
        ac = ActionChains(self.driver)
        x = (i + 0.5) * self.tile_width
        y = (j + 0.5) * self.tile_height
        ac.move_to_element(self.canvas).move_by_offset(-self.canvas_width / 2, -self.canvas_height / 2).move_by_offset(x, y).click().perform()
        time.sleep(0.5)
        self.turn += 1
        if self.is_gameover():
            score_element = self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/h1')
            score = int(score_element.text)
            return True, score

        score_element = self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/span')
        score = int(score_element.text.split(': ')[1])
        return False, score

    def retry(self):
        self.turn = 0
        self.timestamp = datetime.datetime.now().timestamp()
        self.driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div/a[1]/button').click()
        sleep(0.5)
