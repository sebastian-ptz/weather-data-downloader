#!/usr/bin/python3
import requests
import sys
import math
import time
import os

# This script receives weatherdata in JSON-format from OpenWeaterMap API with a web-reuqeusts
# and saves them in a data directory
# API-Source: https://openweathermap.org/history

# Reading API-Key from file
KEYFILE = open("apikey.txt", "r")
API_KEY = KEYFILE.read()
KEYFILE.close()

# Creating needed Unix Timestamps
DATE_FORMAT = "%Y-%m-%d %H:%M %Z"
START_TIME = time.mktime(time.strptime("2023-04-09 23:00 UTC", DATE_FORMAT))
END_TIME = time.mktime(time.strptime("2023-05-06 23:00 UTC", DATE_FORMAT))

ONE_WEEK = 60 * 60 * 24 * 7
DATAPOINT_PER_WEEK = 7 * 24

weeks = []
curr = START_TIME
while curr < END_TIME:
    weeks.append((curr, min(curr + ONE_WEEK, END_TIME)))
    curr += ONE_WEEK
del (curr)
# print(weeks)

latitude_distance = 3.0  # Define how often a point is made
latitude_count = int(1 + 180 / latitude_distance)
# max numvers of points on one hemisphere
max_longitude_count = latitude_count - 1

# Saving data by using less point on poles where latitudes and longitudes are closer
number_of_points_per_lat = [max(1, math.ceil(math.sin(
                            math.pi * lon_index / max_longitude_count) * 
                            max_longitude_count)*2) 
    for lon_index in range(latitude_count)]

# List of Geo-Coordination in a list of latititudes
lat_lists = [[(lat_index * latitude_distance - 90, 
               (360 / number_of_points) * lon_index - 180)
               for lon_index in range(number_of_points)] for lat_index, 
               number_of_points in enumerate(number_of_points_per_lat)]
coords = [point for points in lat_lists for point in points]

invalid_coords = set()

if not os.path.isdir(f"data"):
    os.mkdir("data")
    print(f"Directory data createad...")
else:
    print(f"The direcory data already exists. Using existing directory...")

with open("downloader.log", "w") as log_file:
    for week_index, (START_TIME, END_TIME) in enumerate(weeks):
        print(f"Starting download for week: {week_index + 1} of {len(weeks)}")
        if not os.path.isdir(f"data/{START_TIME}"):
            #directoy with unix timestamp
            os.mkdir(f"data/{START_TIME}") 
        else:
            print(f"\tThe direcory {START_TIME} already exists")

        for index, (lat, lon) in enumerate(coords):
            file_name = f"data/{START_TIME}/{lat}_{lon}.json"
            if os.path.isfile(file_name):
                print(f"\tThe file {file_name} already exists")
                continue
            if (lat, lon) in invalid_coords:
                continue
            url = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={START_TIME}&cnt={DATAPOINT_PER_WEEK}&appid={API_KEY}&units=metric"
            response = requests.get(url)
            log_file.write(f"{url}\r\n")

            # check for errorcodes and add to set invalid_coords l.51
            if response.status_code >= 400:
                log_file.write(
                    f"\tError: {response.status_code} at geo {lat}-{lon}: {response.text}\n")
                print(
                    f"\tError: {response.status_code} at geo {lat}lat {lon}lon: {response.text}", file=sys.stderr)
                invalid_coords.add((lat, lon))
                continue
            with open(f"data/{START_TIME}/{lat}_{lon}.json", "w") as file:
                file.write(response.text)
            print(f"\tDownloaded point: {index + 1} von {len(coords)}")
            