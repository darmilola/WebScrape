import json
import os
import random

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


class RestaurantLinks:

    def __init__(self, link_file='bin/json_data/restaurant_links.json',
                 data_header_details='bin/json_data/data_header_details.json'):
        self.link_file = link_file
        self.link_data = json.load(open(os.path.abspath(self.link_file), 'r'))
        print("Retrieving More Restaurants from Grab Foods")
        print(len(self.link_data['restaurant_links']))
        self.data_header_details = data_header_details
        self.data_header = json.load(open(os.path.abspath(self.data_header_details), 'r'))

    def LoadMoreRestaurant(self, driver, scrapePosition):

        try:
            nextButtton = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ant-btn-block")))

        except TimeoutException:
            driver.close()
            print("Next Button not Available!")

        nextPage = driver.find_element(By.CLASS_NAME, "ant-btn-block")
        # nextPage.click()
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

        # print(len(restaurantList))
        for restaurant in restaurantList[
                          scrapePosition * 8:]:  # always start from multiple of 8 to avoid duplication
            restaurantLink = restaurant.find_element(By.CSS_SELECTOR, 'a').get_attribute(
                'href')  # retrieve link from restaurant list
            LinkList.append(restaurantLink)
        self.add_link(LinkList)
        self.LoadMoreRestaurant(driver, scrapePosition)

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

    def save_link(self):
        with open(self.link_file, 'w') as outfile:
            json.dump(self.link_data, outfile, indent=4)

    def add_link(self, urls=[]):
        for url in urls:
            if url not in self.link_data['restaurant_links']:
                self.link_data['restaurant_links'].append(url)
        self.save_link()

    if __name__ == "__main__":
        pass
