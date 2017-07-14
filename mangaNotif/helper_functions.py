import subprocess
import json


def scrape_manga_data():
    subprocess.call("python manga_scraper.py", shell=True)
    with open('result.json', 'r+') as data_file:
        first_char = data_file.read(1)
        if first_char:
            data_file.seek(0)
            # data = data_file.read()
            manga_data = json.load(data_file)
            print manga_data
            # data_file.seek(0)
            # data_file.truncate()
