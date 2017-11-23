lcd_rss.py

A python RSS feed scroller for a 2-line LCD (or LCD-compatible VFD display).

Based on code from here: https://alvinalexander.com/python/python-script-read-rss-feeds-database

Requires the following external libraries:
feedparser
unidecode
Adafruit_CharLCD

Displays the time on the upper line of the LCD while scrolling news headlines on the bottom line. Updates the news feed every hour in a thread so as not to interrupt time display.
