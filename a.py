
#!/usr/bin/env python
# Author: Yuya Iwabuchi
# Email:  yuya.iwabuchi@gmail.com

import requests
import re
import datetime
import json
import timeit
import os
import sys

URL = 'https://www.utsc.utoronto.ca/~registrar/scheduling/room_schd'
ROOM_URL = 'https://intranet.utsc.utoronto.ca/intranet2/RegistrarService'


def get_html(url, data={}):
    try:
        html = requests.post(url, data=data).text
    except requests.exceptions.SSLError:
        sys.stderr = open(os.devnull, "w")
        html = requests.post(url, data=data, verify=False).text
        sys.stderr = sys.__stderr__
    return html

def collect(date):

    start = timeit.default_timer()
    default_html = get_html(URL)

    post_rooms = ""
    rooms = []

    room_html = re.search('<div id="listRooms".*?</div>', default_html, re.DOTALL).group(0)
    for room in re.findall('value=".*?"', room_html):
        post_rooms += room[7:-1].replace('%20', '-').encode('ascii', 'ignore') + ','
        rooms.append(room[7:-1].replace('%20', '-').encode('ascii', 'ignore'))
    post_rooms = post_rooms[:-1]

    data = {'room': post_rooms,
            'day': date}

    post = get_html(ROOM_URL, data=data).encode('ascii', 'ignore')
    not_found = []
    found = []
    room_data = {'collect': {'collected_on': datetime.datetime.now().strftime('%b %d, %Y'),
                             'collected_week_of': date, 'rooms': rooms}}
    for room in rooms:
        room_regex = ('\"%s":"<table.*?table>' % room)
        try:
            data = re.search(room_regex, post, re.DOTALL).group(0)
            found.append(room)
            room_data[room] = []
        except:
            not_found.append(room)
            continue
        data = re.findall('<tr>.*?tr>', data, re.DOTALL)
        starting_time = re.search("[0-9]{2}:[0-9]{2}", data[1]).group(0)
        offset = int(starting_time[0:2])*2 + (1 if starting_time[3:5] == "30" else 0)
        room_data['collect']['starting_time'] = starting_time

        for i in range(len(data)-1):
            if i == 0:
                for day in re.findall('<th>.*?<\\\\/th>', data[i], re.DOTALL):
                    if len(day) > 10:
                        room_data[room].append([day[4:-6]] + [None]*48)
            else:
                if 'rowspan' in data[i]:
                    days = re.findall('<td.*?<\\\\/td>', data[i], re.DOTALL)
                    same_time = 0
                    for k in range(len(days)):
                        if 'rowspan' in days[k]:
                            rows = int(re.search('rowspan=\'.*?\'', days[k]).group(0)[9:-1])
                            name = re.search('>.*?<', days[k]).group(0)[1:-1]
                            count = 0
                            for j in range(k):
                                if room_data[room][j][i+offset]:
                                    count += 1
                            for l in range(rows):
                                room_data[room][(k - 1) + count - same_time][i+l+offset] = name
                            same_time += 1

    with open('room_data.json', 'w') as f:
        json.dump(room_data, f, indent=4)
    return timeit.default_timer() - start



def find_avail_rooms(room_data, current_time_number, day):
    room_data.pop('collect')
    avail_rooms = []
    for room, data in room_data.iteritems():
        no_class = False
        counter = 0
        while not data[day][current_time_number + counter]:           # FIND DAY
            if current_time_number + counter == 48:
                no_class = True
                break
            counter += 1

        if counter != 0:
            if no_class:
                avail_rooms.append([room, counter, None])
            else:
                avail_rooms.append([room, counter, data[day][current_time_number + counter]])
        else:
            avail_rooms.append([room, counter, data[day][current_time_number + counter]])
    sorted_list = avail_rooms[:]
    sorted_list.sort(key=lambda x: x[0])
    sorted_list.reverse()
    return sorted_list


def display(sorted_list, current_time_block):
    print 'Currently Available Rooms:'
    print '%-9s|%13s  |  %30s' % ('', 'Available', '')
    print '%-9s|%13s  |  %-30s' % ('Room', 'Until', 'Class')
    print '---------|---------------|-----------------------------------'
    for r in sorted_list:
        if r[1] != 0:
            t = str(int(current_time_block[0]) + r[1]//2 +
                    (int(current_time_block[1])//30 + r[1] % 2) // 2) + \
                ':' + '{0:02}'.format(((int(current_time_block[1])//30 +
                r[1]) % 2) * 30)
        else:
            t = 'N/A'

        print '%-9s|%13s  |  %-30s' % (r[0], t, r[2])


def choose_time(time):
    current_time = ['00', '00']
    if time == '':
        current_time = datetime.datetime.now().strftime('%H:%M').split(':')
    elif len(time) <= 2:
        try:
            current_time = [str(int(time)), '00']
        except:
            print 'Invalid Input'
            exit()
    elif len(time) == 3:
        if ':' in time:
            print 'Invalid Input'
            exit()
        try:
            current_time = [str(int(time[0])), '{0:02}'.format(int(time[1:3]))]
        except:
            print 'Invalid Input'
            exit()
    elif len(time) == 4:
        if ':' in time:
            try:
                current_time = [str(int(time[0])), '{0:02}'.format(int(time[1:3]))]
            except:
                print 'Invalid Input'
                exit()
        else:
            try:
                current_time = [str(int(time[0:2])), '{0:02}'.format(int(time[2:4]))]
            except:
                print 'Invalid Input'
                exit()
    elif len(time) == 5:
        if ':' in time:
            try:
                current_time = [str(int(time[0:2])), '{0:02}'.format(int(time[3:5]))]
            except:
                print 'Invalid Input'
                exit()
        else:
            print 'Invalid Input'
            exit()
    else:
        print 'Invalid Input'
        exit()
    current_time_block = [current_time[0], '{0:02}'.format(int(current_time[1])//30 * 30)]
    print('Time: %s:%s\nBlock Time: %s:%s\n' % (current_time[0], current_time[1],
                                                current_time_block[0], current_time_block[1]))
    current_time_number = (int(current_time_block[0]))*2 + int(current_time_block[1])//30 + 1
    return [current_time_number] + current_time_block


def run(time='', day=-1):
    json_date, data = None, None
    try:
        with open('room_data.json') as g:
            data = json.load(g)
            print 'JSON stored date: %s' % data['collect']['collected_on']
            json_date = datetime.datetime.strptime(data['collect']['collected_on'], '%b %d, %Y')
    except:
        pass

    date = datetime.datetime.now().strftime('%Y-%m-%d')
    if day == -1:
        day = (int(datetime.datetime.now().strftime('%w'))-1) % 7
    if not json_date or (json_date + datetime.timedelta(days=1)).date() <= datetime.datetime.now().date():
        print 'The data you have is outdated.\nUpdating data ...',
        os.rename('room_data.json', 'room_data'+datetime.datetime.strftime(json_date, "%Y%m%d")+'.json')
        t = collect(date)
        with open('room_data.json') as g:
            data = json.load(g)
        print 'done! Took %.2fs' % t
        print 'New JSON stored date: %s' % data['collect']['collected_on']

    print 'Day of Week: %i [0=Mon, 6=Sun]' % day
    time = choose_time(time)

    avail_rooms = find_avail_rooms(data, time[0], day)
    display(avail_rooms, time[1:])


if __name__ == '__main__':
    run(time='', day=-1)