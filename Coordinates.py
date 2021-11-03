import json

from bin.getCoordinates import CoordinateScrapper


if __name__ == "__main__":
    coord = CoordinateScrapper()
    coord.start_scrapping()
