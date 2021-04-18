#!/usr/bin/env python


import json

import cv2
import numpy as np

img = cv2.imread('/Users/jim/Dropbox/Documents/Msc/Thesis/A4/Infrared-IPS/configuration/floorplan1.jpg')

# Create blank image with white background

# CV2 works topleft (0,0) need to flip to define co-ordinates in line with other geometry and geographic mapping co-ords
img = cv2.flip(img, flipCode=0)
blankimg = np.zeros(img.shape).astype('uint8')
blankimg = 255 - blankimg
# image scale is 1 pixel per cm
SCALE = 100

# Define Rooms as Bounding Boxes

# It is possible to identify the Hall, Kitchen and Living room seperately using the Saturation peaks
# [10,50], [50,100], [150,200] however using 0 gives good approximation for rooms.
# decided to use colours of rooms to seperate and create polygons for each room in-order to comply with GeoJSON
# meta information about the room including BGR colour for floor background
room_colour_filter = {'kitchen': (226, 211, 202), 'hall': (79, 233, 252), 'livingRoom': (186, 187, 248)}

# References
# To create floor plan
# http://floorplanner.com/projects/21421335-open-plan/edit#assets
# To process image
# http://www.shervinemami.info/blobs.html
# http://opencvpython.blogspot.co.uk/2013/01/contours-5-hierarchy.html
# geojson is used to store the polygons - http://geojsonlint.com


# kernel uses to dilate the extracted images allows joining of hall elements which are split by wall
kernel = np.ones((50, 50), 'uint8')

# create dictionary for room information

# Extract polygons for each room in plan
rooms = {}
for k, v in room_colour_filter.items():
    thresh = cv2.inRange(img, v, v)
    # manipulate image to improve edge detection
    thresh = cv2.dilate(thresh, kernel)
    thresh = cv2.blur(thresh, (10, 10))

    # Get contours for room; Only get external contours
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # there should only be 1
    for a, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        approx = cv2.approxPolyDP(cnt, 10, True)
        rooms[k] = {'bbox': [x, y, w, h], 'cnt': approx.tolist(), 'area': area, 'colour': v}
        # draw on blank image for demonstration purposes
        cv2.drawContours(blankimg, [cnt], -1, v, -1)

# Extract walls - for this we just need the black walls - inverted to search for white lines
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = 255 - gray
gray = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)[1]
gray = cv2.blur(gray, (5, 5))
contours, hierarchy = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

walls = []
for a, cnt in enumerate(contours):
    area = cv2.contourArea(cnt)
    if area > 20000:  # Trial and error shows wall is
        approx = cv2.approxPolyDP(cnt, 10, True)
        cv2.drawContours(img, [approx], -1, (0, 0, 255), 1)
        cv2.drawContours(blankimg, [approx], -1, (0, 0, 0), -1)
        x, y, w, h = cv2.boundingRect(cnt)
        print approx.shape
        walls.append({'bbox': [x, y, w, h], 'cnt': approx.tolist(), 'area': area, 'colour': [0, 0, 0]})

for room in rooms.values():
    x, y, w, h = room['bbox']
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 128, 0), 1)
    cv2.drawContours(img, [np.array(room['cnt'])], -1, room['colour'], 2)
    # cv2.polylines(img,np.array([[x[0] for x in room['cnt']]]),True,(0,255,0),4)

map_objects = {'type': 'FeatureCollection', 'features': [],
               'properties': {'scale': SCALE, 'name': 'IPS Example Floor Plan',
                              'srcImage': '/Users/jim/Dropbox/Documents/Msc/Thesis/A4/Infrared-IPS/location_rules_engine/utilities/floor_plan/floorplan1.jpg',
                              'imageSize': list(img.shape),
                              'position': {'x': 517910, 'y': 204101, 'heading': -21.50,
                                           'referenceFrame': 'eastingNorthing'}}}

for wall in walls:
    x, y, w, h = wall['bbox']
    bbox = [x, y, x + w, h + y]
    map_objects['features'].append(
        {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [[x[0] for x in wall['cnt']]]},
         'properties': {'name':
                            'walls', 'level': 0, 'geomType': 'wall', 'accessible': False, 'colour': (0, 0, 0)},
         'bbox': bbox})

for key, room in rooms.items():
    x, y, w, h = room['bbox']
    bbox = [x, y, x + w, h + y]
    map_objects['features'].append(
        {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [[x[0] for x in room['cnt']]]
                                         }, 'properties': {'name': key,
                                                           'level': 0, 'geomType': 'floor', 'accessible': True,
                                                           'colour': room['colour']}, 'bbox': bbox}
    )

# map_objects = {'scale':SCALE,'floors':[{'floor':'ground_floor','rooms':rooms,'walls':walls}]}
# print map_objects
temp_file = open('/Users/jim/Dropbox/Documents/Msc/Thesis/A4/Infrared-IPS/configuration/floorplan_demo.json', 'wb')
json.dump(map_objects, temp_file)
temp_file.close()

# x,y,w,h = rooms['livingRoom']['bbox']
# blankimg = blankimg[y:y+h,x:x+w]
img = cv2.flip(img, flipCode=0)
blankimg = cv2.flip(blankimg, flipCode=0)
cv2.imshow('img', img)
cv2.imshow('blank', blankimg)
cv2.waitKey()
