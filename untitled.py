import json

import cv2
import numpy as np

img = cv2.imread('./floorplan1.jpg')

blankimg = np.zeros(img.shape).astype('uint8')
blankimg = 255 - blankimg
# image scale is 1 pixel per cm
SCALE = 100

# Define Rooms as Bounding Boxes

# It is possible to identify the Hall, Kitchen and Living room seperately using the Saturation peaks
# [10,50], [50,100], [150,200] however using 0 gives good approximation for rooms.
# decided to use colours of rooms to seperate and create polygons for each room in-order to comply with GeoJSON


# References
# To create floor plan
# http://floorplanner.com/projects/21421335-open-plan/edit#assets
# To process image
# http://www.shervinemami.info/blobs.html
# http://opencvpython.blogspot.co.uk/2013/01/contours-5-hierarchy.html
# json is used to store the polygons


room_colour_filter = {'kitchen': (226, 211, 202), 'hall': (79, 233, 252), 'living_room': (186, 187, 248)}
kernel = np.ones((50, 50), 'uint8')
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

# Define Walls
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = 255 - gray
gray = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)[1]
gray = cv2.blur(gray, (5, 5))
contours, hierarchy = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

walls = []
for a, cnt in enumerate(contours):
    area = cv2.contourArea(cnt)
    if area > 20000:
        approx = cv2.approxPolyDP(cnt, 1, True)
        cv2.drawContours(img, [approx], -1, (0, 0, 255), 1)
        cv2.drawContours(blankimg, [approx], -1, (0, 0, 0), -1)
        print approx.shape
        walls.append(approx.tolist())

for room in rooms.values():
    x, y, w, h = room['bbox']
    cv2.rectangle(img, (x, y), (xw, yh), (0, 128, 0), 1)
    cv2.drawContours(img, [np.array(room['cnt'])], -1, room['colour'], 2)

map_objects = {'scale': SCALE, 'floors': [{'floor': 'ground_floor', 'rooms': rooms, 'walls': walls}]}
# print map_objects
temp_file = open('./floorplan1.json', 'wb')
json.dump(map_objects, temp_file)
temp_file.close()

x, y, w, h = rooms['living_room']['bbox']
blankimg = blankimg[y:yh, x:xw]

cv2.imshow('img', img)
cv2.imshow('blank', blankimg)
cv2.waitKey()

