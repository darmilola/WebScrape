import os
import re
import string
import time

import selenium
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC, wait
import json
from selenium.webdriver.common.keys import Keys
from time import sleep

currentPageIndex = 0

s = Service(executable_path='C:/Users/user/Downloads/chromedriver_win32/chromedriver.exe')
driver = webdriver.Chrome(service=s)


def PrepareInput():
    driver.get('https://food.grab.com/ph/en/restaurants')
    try:
        mAddressBar = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sectionContent___2XGJB")))

    except TimeoutException:
        # If the loading took too long, print message and try again
        print("AddressBar not Available!")

    addressBarInput = driver.find_element(By.CLASS_NAME, "sectionContent___2XGJB")
    addressBarInput.click()

    try:
        mSearchBar = WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.ID, "location-input")))

    except TimeoutException:
        # If the loading took too long, print message and try again
        print("Location Input not Available!")

    searchBar = driver.find_element(By.ID, "location-input")
    searchBar.send_keys("Avida Towers Asten Tower 1 - Malugay St, San Antonio, Makati, Metro Manila, NCR, 1226, Philippines")


PrepareInput()


def ScrapePage(link):

    driver = webdriver.Chrome(service=s)
    driver.get(link)

    restaurantId = re.search('[^/]*$', link)

    try:
        mRestaurant = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "__NEXT_DATA__")))

    except TimeoutException:
        # If the loading took too long, print message and try again
        print("Next Data not Available!")

    nextData = driver.find_element(By.ID, "__NEXT_DATA__")
    scriptJson = nextData.get_attribute("innerHTML")
    json_dict = json.loads(scriptJson)
    props = json_dict['props']
    reduxState = props['initialReduxState']
    restaurantDetail = reduxState['pageRestaurantDetail']
    entities = restaurantDetail['entities']
    restaurantkey = entities[restaurantId.group()]
    latLng = restaurantkey['latlng']
    print('Shop Id is {} Latitude is {} Longitude is {}"'.format(restaurantId.group(), latLng['latitude'],
                                                                 latLng['longitude']))
    driver.close()


def SetUpPageScrape(scrapePosition):
    LinkList = []
    print("Scrape Position is ", scrapePosition)
    try:
        mRestaurant = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "RestaurantListCol___1FZ8V")))
    except TimeoutException:
        print("Restaurant List not Available!")

    restaurantList = driver.find_elements(By.CLASS_NAME, "RestaurantListCol___1FZ8V")

    print(len(restaurantList))
    for restaurant in restaurantList[scrapePosition*8:]:
        restaurantLink = restaurant.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
        LinkList.append(restaurantLink)
        # startPosition = currentPageIndex * 8
        # ScrapePage(restaurantLink)
    print("Link len is ", len(LinkList))
    for link in LinkList:
        ScrapePage(link)

    restaurantList.clear()
    LoadMoreRestaurant()


def LoadMoreRestaurant():
    try:
        nextButtton = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ant-btn-block")))

    except TimeoutException:
        print("Next Button not Available!")

    nextPage = driver.find_element(By.CLASS_NAME, "ant-btn-block")
    webdriver.ActionChains(driver).move_to_element(nextPage).click(nextPage).perform()
    driver.implicitly_wait(0)
    WebDriverWait(driver, 20).until(EC.invisibility_of_element_located((By.CLASS_NAME, "dot___2NCjm")))
    global currentPageIndex
    currentPageIndex = currentPageIndex + 1
    SetUpPageScrape(currentPageIndex)
    # time.sleep(10)
    # WebDriverWait.until(lambda driver: driver.execute_script("return jQuery.active == 0"))
    # nextLoading = driver.find_elements(By.CLASS_NAME, "loading___16cX8")


SetUpPageScrape(0)










