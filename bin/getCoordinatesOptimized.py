import asyncio
import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread


class Optimized:
    def __init__(self, coordinates_file='bin/json_data/coordinates.json',
                 data_header_details='bin/json_data/data_header_details.json'):
        self.coordinates_file = coordinates_file
        self.data_header_details = data_header_details
        self.url_max_retries = 5
        self.max_retries = 5
        self.max_workers = 100
        self.timeout = 10
        self.coordinates_data = json.load(open(os.path.abspath(self.coordinates_file), 'r'))
        self.data_header = json.load(open(os.path.abspath(self.data_header_details), 'r'))

    async def LoadMoreRestaurant(self, driver, scrapePosition):

        try:
            nextButton = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ant-btn-block")))

        except TimeoutException:
            print("Next button no more available")
            driver.close()

        nextPage = driver.find_element(By.CLASS_NAME, "ant-btn-block")
        webdriver.ActionChains(driver).move_to_element(nextPage).click(nextPage).perform()
        WebDriverWait(driver, 20).until(
            EC.invisibility_of_element_located(
                (By.CLASS_NAME, "dot___2NCjm")))  # wait for loading indicator to disappear

        scrapePosition = scrapePosition + 1
        self.get_restaurant_links(driver, scrapePosition)

    def get_restaurant_links(self, driver, scrapePosition):
        LinkList = []

        try:
            mRestaurant = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "RestaurantListCol___1FZ8V")))
        except TimeoutException:
            print("Restaurant List not Available!")

        # retrieve all restaurant with the class name
        restaurantList = driver.find_elements(By.CLASS_NAME, "RestaurantListCol___1FZ8V")

        for restaurant in restaurantList[
                          scrapePosition * 8:]:  # always start from multiple of 8 to avoid duplication
            restaurantLink = restaurant.find_element(By.CSS_SELECTOR, 'a').get_attribute(
                'href')  # retrieve link from restaurant list
            LinkList.append(restaurantLink)
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.start_scrapping(LinkList))  # start scraping coordinates in batches of 8
        asyncio.ensure_future(self.LoadMoreRestaurant(driver, scrapePosition))
        loop.run_forever()

    def LoadRestaurant(self):
        s = Service(
            executable_path='C:/Users/user/Downloads/chromedriver_win32/chromedriver.exe')

        mProxy = self.data_header['working_proxies'][
            random.randint(0, len(self.data_header['working_proxies']) - 1)]

        options = {
            'proxy': {
                'http': 'http://' + mProxy,
                'https': 'https://' + mProxy,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(service=s, seleniumwire_options=options)
        # driver.request_interceptor = self.mInterceptor
        driver.get("https://food.grab.com/ph/en/restaurants")
        self.get_restaurant_links(driver, 0)

    def mInterceptor(self, request):
        del request.headers['user-agent']
        del request.headers['referer']
        del request.headers['Upgrade-Insecure-Requests']
        del request.headers['DNT']
        del request.headers['Connection']
        del request.headers['Accept']
        del request.headers['Accept-Encoding']
        del request.headers['Accept-Language']
        request.headers['user-agent'] = self.data_header['user_agents_scrap'][
            random.randint(0, len(self.data_header['user_agents_scrap']) - 1)]
        request.headers['referer'] = self.data_header['referrer'][
            random.randint(0, len(self.data_header['referrer']) - 1)]
        request.headers['Upgrade-Insecure-Requests'] = '0'
        request.headers['DNT'] = '1'
        request.headers['Connection'] = 'keep-alive'
        request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        request.headers['Accept-Encoding'] = 'gzip, deflate, br'
        request.headers['Accept-Language'] = 'en-US,en;q=0.5'

    def ScrapePage(self, link):

        s = Service(
            executable_path='C:/Users/user/Downloads/chromedriver_win32/chromedriver.exe')

        mProxy = self.data_header['working_proxies'][
            random.randint(0, len(self.data_header['working_proxies']) - 1)]

        options = {
            'proxy': {
                'http': 'http://' + mProxy,
                'https': 'https://' + mProxy,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(service=s, seleniumwire_options=options, chrome_options=chrome_options)
        driver.request_interceptor = self.mInterceptor
        driver.get(link)
        restaurantId = re.search('[^/]*$', link)  # using regex to retrieve restaurant Id from the url

        try:
            mRestaurant = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
            # wait till __NEXT_DATA__ ID is available

        except TimeoutException:
            return '0'
            print("Next Data not Available!")

        # move through  __NEXT_DATA__ innerHTML json to retrieve restaurant latitude and longitude
        nextData = driver.find_element(By.ID, "__NEXT_DATA__")
        scriptJson = nextData.get_attribute("innerHTML")
        json_dict = json.loads(scriptJson)
        props = json_dict['props']
        reduxState = props['initialReduxState']
        restaurantDetail = reduxState['pageRestaurantDetail']
        entities = restaurantDetail['entities']
        restaurantkey = entities[restaurantId.group()]
        latLng = restaurantkey['latlng']
        data = {}
        data['Id'] = restaurantId.group()
        data['latitude'] = latLng['latitude']
        data['longitude'] = latLng['longitude']
        json_data = json.dumps(data)
        self.add_coordinates(json_data)
        print('Shop Id is {} Latitude is {} Longitude is {}"'.format(restaurantId.group(), latLng['latitude'],
                                                                     latLng['longitude']))
        driver.close()
        return {'link': restaurantId.group()}

    def save_coordinates(self):
        with open(self.coordinates_file, 'w') as outfile:
            json.dump(self.coordinates_data, outfile, indent=4, sort_keys=True)

    def add_coordinates(self, coordinate):
        if coordinate not in self.coordinates_data['restaurant_coordinates']:
            self.coordinates_data['restaurant_coordinates'].append(coordinate)
            self.save_coordinates()

    async def get_batch_coordinates(self, linkList):
        flag = self.max_retries
        while flag:
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    loop = asyncio.get_event_loop()
                    tasks = [
                        loop.run_in_executor(executor, self.ScrapePage, link)
                        for link in linkList
                    ]

                    for response in await asyncio.gather(*tasks):
                        if response != '0':
                            linkList.remove(response['link'])

                    if len(linkList) == 0:
                        flag = 0
                    else:
                        flag -= 1
            except Exception as E:
                print(
                    'Scrapping Went Wrong -> {} Lineno. -> {}'.format(E, sys.exc_info()[-1].tb_lineno))

    async def start_scrapping(self, linkList):
        print('Retrieving restaurants coordinates from url')
        try:
            self.loop = asyncio.get_event_loop()
            self.loop.set_debug(1)
            future = asyncio.ensure_future(self.get_batch_coordinates(linkList))
            self.loop.run_until_complete(future)
        except Exception as E:
            print('Warning Log -> {} Lineno -> {}'.format(E, sys.exc_info()[-1].tb_lineno))
        finally:
            self.loop.close()
        print("Scrapping done successfully, data stored in coordinates.json file")
