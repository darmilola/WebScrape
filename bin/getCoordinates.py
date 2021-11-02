import json
import os
import random
import re

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC


class CoordinateScrapper:

    def __init__(self, coordinates_file='bin/json_data/coordinates.json', link_file='bin/json_data/restaurant_links.json',
                 data_header_details='bin/json_data/data_header_details.json'):
        self.link_file = link_file
        self.coordinates_file = coordinates_file
        self.data_header_details = data_header_details
        self.link_data = json.load(open(os.path.abspath(self.link_file), 'r'))
        self.coordinates_data = json.load(open(os.path.abspath(self.coordinates_file), 'r'))
        self.data_header = json.load(open(os.path.abspath(self.data_header_details), 'r'))

    def get_coordinates(self):
        for link in self.link_data['restaurant_links']:
            if link not in self.link_data['success_links']:
               self.ScrapePage(link)

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

        #chrome_options = webdriver.ChromeOptions()
        #chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(service=s, seleniumwire_options=options)
        driver.request_interceptor = self.mInterceptor
        driver.get(link)


        restaurantId = re.search('[^/]*$', link)  # using regex to retrieve restaurant Id from the url

        try:
            mRestaurant = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))
            # wait till __NEXT_DATA__ ID is available

        except TimeoutException:
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
        self.add_success_link(link)
        print('Shop Id is {} Latitude is {} Longitude is {}"'.format(restaurantId.group(), latLng['latitude'],
                                                                     latLng['longitude']))
        driver.close()

    def save_coordinates(self):
        with open(self.coordinates_file, 'w') as outfile:
            json.dump(self.coordinates_data, outfile, indent=4, sort_keys=True)

    def add_coordinates(self, coordinate):
        if coordinate not in self.coordinates_data['restaurant_coordinates']:
           self.coordinates_data['restaurant_coordinates'].append(coordinate)
           self.save_coordinates()

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

    def save_success_link(self):
        with open(self.link_file, 'w') as outfile:
            json.dump(self.link_data, outfile, indent=4)

    def add_success_link(self, link):
        self.link_data['success_links'].append(link)
        self.save_success_link()