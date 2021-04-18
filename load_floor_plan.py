__author__ = 'jim'


#!/usr/bin/env python
import json
import sys
import copy

import cv2
import numpy as np
from shapely.geometry import Polygon # http://toblerity.org/shapely/manual.html
import shapely


FILE = '/Users/jim/Dropbox/Documents/Msc/Thesis/A4/Infrared-IPS/configuration/floorplan1.json'


def load_map(file_name):
    """load map for specified room"""
    map_data = {}
    try:
        with open(file_name,'r') as fs:
            map_data = json.load(fs)
    except IOError as e:
        print ("I/O error({0}): {1}".format(e.errno, e.strerror))
    except:
        print ("Unexpected error:", sys.exc_info()[0],sys.exc_info()[1])
    return map_data

def create_intersection_polygon(wall_polygon,bbox_poly):
    return_value = {}

    my_shapley_bbox = Polygon(bbox_poly)
    my_shapley_walls = Polygon(wall_polygon[0]) # Exterior of wall Polygon only.
    my_shapley_room_walls = my_shapley_bbox.intersection(my_shapley_walls)

    if isinstance(my_shapley_room_walls,shapely.geometry.multipolygon.MultiPolygon):
        return_value = {'type':'MultiPolygon'}
        return_value['coordinates'] = []
        for my_shaply_poly in my_shapley_room_walls:
            return_value['coordinates'].append([[list(map(int,a)) for a in  my_shaply_poly.exterior.coords]])

    else:
        return_value['type'] ='Polygon'
        return_value['coordinates'] = [[list(map(int,a)) for a in my_shapley_room_walls.exterior.coords]]

    return return_value

def translate_map(map_data,bbox):
    """utility function to move co-ordinates in map_data to a new origin in top left corner of bounding box"""
    x1,y1,x2,y2 = bbox
    map_data['properties']['originalBBox'] = bbox
    map_data['properties']['imageSize']=[y2-y1,x2-x1,map_data['properties']['imageSize'][2]]

    for feature in map_data['features']:
        if 'bbox' in feature.keys():
            if feature['properties']['geomType'] == 'wall':
                feature['bbox']=[0,0,x2-x1,y2-y1]
            else:
                feature['bbox']= [feature['bbox'][0]-x1,feature['bbox'][1]-y1,feature['bbox'][2]-x1,feature['bbox'][3]-y1]

        if feature['geometry']['type']=='Polygon':
            for i,linearring in  enumerate(feature['geometry']['coordinates']):
                feature['geometry']['coordinates'][i] = [[x[0]-x1,x[1]-y1] for x in linearring]
        elif feature['geometry']['type']=='MultiPolygon':
            for i, polygon in enumerate(feature['geometry']['coordinates']):
                for j,linearring in  enumerate(polygon):
                    feature['geometry']['coordinates'][i][j] = [[x[0]-x1,x[1]-y1] for x in linearring]
    return map_data

def get_room_details(map_data,room):
    """extract polygon data for room with origin set to top left of bounding box"""
    room_return_value = {}
    return_value = map_data
    return_value['properties']['name'] = 'Map Data filtered for ' + room

    try:
        room_return_value['features'] = [map_data['features'][[i for i,f in enumerate(map_data['features']) if f['properties']['name'] == room ][0]]]

        #Get bounding box details for floor and create a polygon linearring
        x1,y1,x2,y2 = room_return_value['features'][0]['bbox']
        bbox_poly = [[x1,y1],[x1,y2],[x2,y2],[x2,y1]]

        #cnt(room_data['walls']['geometry']['coordinates']).tolist()[0]

        #get walls for room and translate to new origin bbox = (0,0)
        walls = map_data['features'][[i for i,f in enumerate(map_data['features']) if f['properties']['name'] == 'walls' ][0]]

        if walls['geometry']['type'] == 'MultiPolygon':
            multi_walls = []
            for i, wall_polygon in  enumerate(walls['geometry']['coordinates']):
                multi_walls.append(create_intersection_polygon(walls['geometry']['coordinates'][i], bbox_poly)['coordinates'])
            walls['geometry']['coordinates']=multi_walls

        elif walls['geometry']['type'] == 'Polygon':
             walls['geometry'] = create_intersection_polygon(walls['geometry']['coordinates'],bbox_poly)

        else:
            raise ValueError('Walls not Polygon as expected')

        room_return_value['features'].append(walls)
        return_value['features'] = room_return_value['features']


    except IndexError:
        print ("Index error:", sys.exc_info()[0], sys.exc_info()[1])
        return_value = {}
    except:
        print ("Unexpected error:", sys.exc_info()[0],  sys.exc_info()[1])
        return_value = {}

    return return_value

def draw_map_data(map_data):
    blankimg = 255-np.zeros(tuple(map_data['properties']['imageSize'])).astype('uint8')
    floors = []
    walls = []

    cnt = lambda y: [np.array(x) for x in y]

    def extract_linearring(polygon,walls,floors,geom_type):
        for linearring in polygon:
            if geom_type == 'floor':
                floors.append([linearring])
            elif geom_type == 'wall':
                walls.append([linearring])
            else:
                raise ValueError('unexpected geomType found:' + geom_type)

    for feature in map_data['features']:
        if feature['geometry']['type']=='Polygon':
            extract_linearring(feature['geometry']['coordinates'],walls,floors,feature['properties']['geomType'])
        elif feature['geometry']['type']=='MultiPolygon':
            for polygon in feature['geometry']['coordinates']:
                extract_linearring(polygon,walls,floors,feature['properties']['geomType'])

    cv2.fillPoly(blankimg,cnt(floors),(128,128,128))
    cv2.fillPoly(blankimg,cnt(walls),(0,0,0))

    blankimg = cv2.flip(blankimg,flipCode=0)
    cv2.imshow(map_data['properties']['name'],blankimg)

if __name__ == '__main__':
    map_data = load_map(FILE)
    draw_map_data(map_data)
    print ('map data -->', map_data)
    print ('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
    rooms = ['junk','kitchen','livingRoom','hall']

    for room in rooms:
        room_data = get_room_details(copy.deepcopy(map_data),room)
        # Need to create a new object to be passed to the get_room_details function to prevent the original
        # map_data object being manipulated by the function using a different name. As dictionaries are mutable http://python.net/~goodger/projects/pycon/2007/idiomatic/handout.html#other-languages-have-variables

        print (room,':pre translation room data -->', json.dumps(room_data))
        print ('-=-=-=-=')
        if room_data:
            bbox = room_data['features'][[i for i,f in enumerate(room_data['features']) if f['properties']['name'] == room ][0]]['bbox']
            room_data = translate_map(copy.deepcopy(room_data),bbox)

            print (room,':post translation room data -->', json.dumps(room_data))

            draw_map_data(room_data)

            print ('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')

    # Ensure that function can deal with Multiple Polygons
    room_data = get_room_details(room_data,room)
    print ('hall using ammended map - room data -->', json.dumps(room_data))
    print ('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')

    print ('hall using ammended map - room data -->', json.dumps(room_data))

    cv2.waitKey(0)