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


def PrepareInput(driver, location):
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
    searchBar.send_keys(location)


def ScrapePage(link):

    driver = webdriver.Chrome(service=s)
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
    print('Shop Id is {} Latitude is {} Longitude is {}"'.format(restaurantId.group(), latLng['latitude'],
                                                                 latLng['longitude']))
    driver.close()


def SetUpPageScrape(scrapePosition, driver):
    LinkList = []
    # print("Scrape Position is ", scrapePosition)
    try:
        mRestaurant = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "RestaurantListCol___1FZ8V")))
    except TimeoutException:
        print("Restaurant List not Available!")

    # retrieve all restaurant with the class name
    restaurantList = driver.find_elements(By.CLASS_NAME, "RestaurantListCol___1FZ8V")

    # print(len(restaurantList))
    for restaurant in restaurantList[scrapePosition*8:]:  # always start from multiple of 8 to avoid duplication
        restaurantLink = restaurant.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') # retrieve link from restaurant list
        LinkList.append(restaurantLink)
    # print("Link len is ", len(LinkList))
    for link in LinkList:
        ScrapePage(link) # scrape each link available

    restaurantList.clear()  # clear old restaurant from list
    LoadMoreRestaurant(driver) # load more restaurant if available


def LoadMoreRestaurant(driver):
    try:
        nextButtton = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ant-btn-block")))

    except TimeoutException:
        print("Next Button not Available!")

    nextPage = driver.find_element(By.CLASS_NAME, "ant-btn-block")
    webdriver.ActionChains(driver).move_to_element(nextPage).click(nextPage).perform()
    driver.implicitly_wait(0)
    WebDriverWait(driver, 20).until(EC.invisibility_of_element_located((By.CLASS_NAME, "dot___2NCjm"))) # wait for loading indicator to disappear
    global currentPageIndex
    currentPageIndex = currentPageIndex + 1
    SetUpPageScrape(currentPageIndex, driver)


def LoadInAddress(driver):
    # startLetter = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "O", "Q", "R", "S", "T", "U", "V", "W", "X", "Y","Z"]
    addressText = []
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
    searchBar.send_keys("A") # retrieving address based on prediction using first letter as initial, A - Z can be used
    WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.CLASS_NAME, "ant-select-dropdown-menu-item")))  # wait for dropdown to be visible
    locationDropdownList = driver.find_elements(By.CLASS_NAME, "ant-select-dropdown-menu-item")

    for location in locationDropdownList:
        addressText.append(location.text)

    return addressText


if __name__ == "__main__":
    s = Service(executable_path='C:/Users/user/Downloads/chromedriver_win32/chromedriver.exe') # Change to chromedriver path
    driver = webdriver.Chrome(service=s)
    currentPageIndex = 0
    mAddress = LoadInAddress(driver)
    for addressText in mAddress:
        PrepareInput(driver, addressText)
        SetUpPageScrape(0, driver)












