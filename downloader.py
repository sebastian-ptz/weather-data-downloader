#!/usr/bin/python3
import requests
import sys
import math
import time
import os

#This script receives weatherdata in JSON-format from OpenWeaterMap API with a web-reuqeusts and saves them in a data directory
#API-Source: https://openweathermap.org/history

#Reading API-Key from file
keyfile = open("apikey.txt", "r")
api_key = keyfile.read()
keyfile.close()

#Creating needed Unix Timestamps
date_format = "%Y-%m-%d %H:%M %Z"
start_time = time.mktime(time.strptime("2023-03-31 23:00 UTC", date_format))
end_time = time.mktime(time.strptime("2023-04-30 23:00 UTC", date_format))

one_week = 60 * 60 * 24 * 7
datapoints_per_week = 7 * 24

weeks = []
curr = start_time
while curr < end_time:
  weeks.append((curr, min(curr + one_week, end_time)))
  curr += one_week
del(curr)
#print(weeks)

latitude_precision = 2 # Define precise a point is made
latitude_count = int(1 + 180 / latitude_precision)
max_longitude_count = latitude_count - 1 # max num. of points on one hemisphere

# Saving data by using less point on poles where latitude and longitudes are closer to each other
number_of_points_per_lat = [max(1, math.ceil(math.sin(math.pi * lon_index / max_longitude_count) * max_longitude_count)*2) for lon_index in range(latitude_count)]

# List of Geo-Coordination
point_lists = [[((lat_index * latitude_precision) - 90, (360 / numberOfPoints) * lon_index - 180) for lon_index in range(numberOfPoints) ] for lat_index, numberOfPoints in enumerate(number_of_points_per_lat)]
#print([len(x) for x in point_lists])
points = [point for points in point_lists for point in points]

invalid_points = set()

#os.mkdir("data")
with open("downloader.log", "w") as log_file:
  for week_index, (start_time, end_time) in enumerate(weeks): # enumerate weeks of month
    print(f"Starting download for week: {week_index + 1} of {len(weeks)}")
    if not os.path.isdir(f"data/{start_time}"):
      os.mkdir(f"data/{start_time}") # mkdir with unix timestamp for the start of a week
    else:
      print(f"The direcory {start_time} already exists")
      
    for point_index, (lat, lon) in enumerate(points): # enemurate geo-points
      file_name = f"data/{start_time}/{lat}_{lon}.json"
      if os.path.isfile(file_name):
        print(f"The file {file_name} already exists")
        continue
      if (lat, lon) in invalid_points:
        continue
      url = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start_time}&cnt={datapoints_per_week}&appid={api_key}&units=metric"
      response = requests.get(url)
      log_file.write(f"{url}\r\n")

      # check for errors, adding points with errors to the set invalid_points l. 44
      if response.status_code >= 400: 
        log_file.write(f"Error: {response.status_code} at geo {lat}-{lon}: {response.text}\r\n")
        print(f"Error: {response.status_code} at geo {lat}-{lon}: {response.text}", file=sys.stderr)
        invalid_points.add((lat, lon))
        continue
      with open(f"data/{start_time}/{lat}_{lon}.json", "w") as file:
        file.write(response.text)
      print(f"\tDownloaded point: {point_index + 1} von {len(points)}")
