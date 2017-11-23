#!/usr/bin/python

import os
import feedparser
import time
from time import sleep, strftime
from datetime import datetime
from subprocess import check_output
import sys
import unidecode
import Adafruit_CharLCD as LCD
from threading import Thread
from Queue import Queue

feed_name = 'breitbart'
url = 'http://feeds.feedburner.com/breitbart'

#feed_name = sys.argv[1]
#url = sys.argv[2]

db = '/var/tmp/feeds.db'
limit = 12 * 3600 * 1000

# globals for get_feed() so it can run as a thread
# and have a place to return data
posts_to_print = []
posts_to_skip = []


# function to get the current time
#
current_time_millis = lambda: int(round(time.time() * 1000))
current_timestamp = current_time_millis()

def post_is_in_db(title):
    with open(db, 'r') as database:
        for line in database:
            if title in line:
                return True
    return False

# return true if the title is in the database with a timestamp > limit
def post_is_in_db_with_old_timestamp(title):
    with open(db, 'r') as database:
        for line in database:
            if title in line:
                ts_as_string = line.split('|', 1)[1]
                ts = long(ts_as_string)
                if current_timestamp - ts > limit:
                    return True
    return False

def get_feed():
    while True:
        # get the feed data from the url
        #
        feed = feedparser.parse(url)
            
        
        #
        # figure out which posts to print
        #
        global posts_to_print 
        global posts_to_skip
        
        for post in feed.entries:
            # if post is already in the database, skip it
            # TODO check the time
            title = post.title
            if post_is_in_db_with_old_timestamp(title):
                posts_to_skip.append(title)
            else:
                posts_to_print.append(title)
            
        #
        # add all the posts we're going to print to the database with the current timestamp
        # (but only if they're not already in there)
        #
        f = open(db, 'a')
        for title in posts_to_print:
            if not post_is_in_db(title):
                title.encode('utf-8','replace')
                f.write(unidecode.unidecode(title) + "|" + str(current_timestamp) + "\n")
        f.close
        # sleep for one hour
        time.sleep(3600)

def wrapper(func, queue):
    queue.put(func())

q1 = Queue()
    
# Raspberry Pi pin configuration:
lcd_rs        = 27  # Note this might need to be changed to 21 for older revision Pi's.
lcd_en        = 22
lcd_d4        = 25
lcd_d5        = 24
lcd_d6        = 23
lcd_d7        = 18
lcd_backlight = 26 

# BeagleBone Black configuration:
# lcd_rs        = 'P8_8'
# lcd_en        = 'P8_10'
# lcd_d4        = 'P8_18'
# lcd_d5        = 'P8_16'
# lcd_d6        = 'P8_14'
# lcd_d7        = 'P8_12'
# lcd_backlight = 'P8_7'

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 20
lcd_rows    = 2

MAX_FPS = 6

class scroller(object):

    left_spaces = 20
    left_start = 0
    right_end = 1
    right_spaces = 1
    line = 1
    spaces_from_left = 20

    def __init__(self, lcd_columns = 20, line = 1):
        self.lcd_columns = lcd_columns
        self.line = line
        
    def step(self, scroll_string):
        self.scroll_string = scroll_string

        # string equal to or larger than the display
        if (len(self.scroll_string) >= self.lcd_columns):
            # first just blank the line
            if (self.left_spaces == self.lcd_columns):
                lcd.set_cursor(0, self.line)
                lcd.message(' ' * self.left_spaces)
                self.left_spaces -= 1
                return 1
            # scroll on from the right
            # until the left side of the display
            elif (self.left_spaces > 0):
                lcd.set_cursor(0, self.line)
                lcd.message(' ' * self.left_spaces +  self.scroll_string[self.left_start:self.right_end])
                self.right_end += 1
                self.left_spaces -= 1
                return 1
            # scroll until the end of the string is on
            # the right side of the display
            elif (self.right_end < len(self.scroll_string)):
                lcd.set_cursor(0, self.line) 
                lcd.message(self.scroll_string[self.left_start:self.right_end])
                self.left_start += 1
                self.right_end += 1
                return 1
            # scroll until the end of the string is on
            # the left side of the display
            elif (self.right_spaces <= self.lcd_columns):
                lcd.set_cursor(0, self.line)
                lcd.message(self.scroll_string[self.left_start:self.right_end] + ' ' * self.right_spaces)
                self.left_start += 1
                self.right_spaces += 1 
                return 1
            # blank the line and signal that scrolling is done
            else:
                lcd.set_cursor(0, self.line)
                lcd.message(' ' * self.lcd_columns)
                self.left_spaces = self.lcd_columns
                self.left_start = 0
                self.right_end = 1
                self.right_spaces = 1
                self.spaces_from_left = self.lcd_columns 
                return 0
        else:
            # first just blank the line
            if (self.left_spaces == self.lcd_columns): 
                lcd.set_cursor(0, self.line)
                lcd.message(' ' * self.left_spaces)
                self.left_spaces -= 1
                self.spaces_from_left -= 1
                return 1
            # scroll on from the right
            # until the end of the string is at the right end of the display
            elif (self.spaces_from_left >= (self.lcd_columns - (len(self.scroll_string)))):
                lcd.set_cursor(0, self.line)
                lcd.message(' ' * self.spaces_from_left + self.scroll_string[0:self.right_end])
                self.right_end += 1
                self.spaces_from_left -= 1
                return 1
            # scroll until the start of the string is on
            # the left side of the display
            elif (self.spaces_from_left > 0):
                lcd.set_cursor(0, self.line)
                lcd.message(' ' * self.spaces_from_left + self.scroll_string + ' ' * self.right_spaces)
                self.spaces_from_left -= 1
                self.right_spaces += 1
                return 1
            # scroll until the end of the string is on
            # the left side of the display
            elif (self.right_spaces < self.lcd_columns):
                lcd.set_cursor(0, self.line)
                lcd.message(self.scroll_string[self.left_start:self.right_end] + ' ' * self.right_spaces)
                self.left_start += 1
                self.right_spaces += 1 
                return 1
            # blank the line and signal that scrolling is done 
            else:   
                lcd.set_cursor(0, self.line)
                lcd.message(' ' * self.lcd_columns) 
                self.left_spaces = self.lcd_columns 
                self.left_start = 0
                self.right_end = 1
                self.right_spaces = 1
                self.spaces_from_left = self.lcd_columns 
                return 0 
    
    def check(self):
        lcd.clear()
        lcd.set_cursor(0, 0)
        lcd.message("LINE ONE")
        lcd.set_cursor(0, 1)
        lcd.message("LINE TWO")


# Initialize the LCD using the pins above.
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                           lcd_columns, lcd_rows, lcd_backlight)

s = scroller(20, 1)

lcd.clear()
lcd.vfd_dim(3)
# Print a two line message
lcd.message('Pi Clock\nRSS Scroller')

# Wait 5 seconds
time.sleep(5.0)

# set the seconds to something that will never match
# so that we update the time the first time through
tempSecond = 60

lastTime = 0

minuteCount = 0

# set the minutes initially to something that will never match
# so that we will update the RSS feed immediately the first time through
tempMin = 60

# it takes a bit to parse a feed
# so tell the user what's going on
lcd.clear()
lcd.message("Getting posts\nPlease be patient")

# how many posts
numPosts = len(posts_to_print)
# post counter
postCount = 0

# track if scrolling done
is_scoll_done = 0

# track scrolling step time or FPS
lastTime = time.time()
# track if new frame
new_frame_now = 1

# an offset to position the start of the time on the display
# to even out wear on the VFD
offset = 0

# start the feed thread
Thread(target = wrapper, args=(get_feed, q1)).start()

# it takes a bit to parse a feed
# so tell the user what's going on
lcd.clear()
lcd.message("Getting posts\nPlease be patient")

# wait for a bit so the feed thread
# has time to fetch something
# wait 5 minutes
time.sleep(300)

# main loop
while (True):
    # count each minute as it changes 
    if tempMin != datetime.now().strftime('%M'): 
        tempMin = datetime.now().strftime('%M')
        # see if 15 minutes is elapsed
        if minuteCount == 15:
            minuteCount = 0
            # move the time display to the right
            if offset < 4:
                offset += 1
            # go back to the left side of the display
            else:
                lcd.set_cursor(0, 0)
                lcd.message("                    ")
                offset = 0
        # increment minute count
        minuteCount = minuteCount + 1

    # update the time every second
    if tempSecond != datetime.now().strftime('%S'):
        tempSecond = datetime.now().strftime('%S') 
        lcd.set_cursor(0, 0)
        lcd.message(' ' * offset + datetime.now().strftime('%b %d  %H:%M:%S'))

    
    # check how many posts and compare to postCount
    # do it every time since we don't know when get_feed will complete
    # as it is called in a seprate thread    
    numPosts = len(posts_to_print)
    # start over if posts have decreased
    if postCount > numPosts:
        postCount = 0;       
 
    if (new_frame_now == 1):
        new_frame_now = 0
        if (s.step(posts_to_print[postCount])) == 0:
            if (postCount < (numPosts - 1)):
                postCount += 1
            else:
                postCount = 0
   
    # see if it is time to update the frame
    if (time.time() - lastTime) > (1.0 / MAX_FPS):
        lastTime = time.time()
        new_frame_now = 1
