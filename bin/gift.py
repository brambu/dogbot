#!/usr/bin/env python

#!/usr/bin/env python

from argparse import ArgumentParser
import sys
import logging
import random
import feedparser
import urllib2
from HTMLParser import HTMLParser

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def gift_fetch(url):
  try:
    feed = feedparser.parse(url)
  except:
    log.warn('cannot fetch from %s' % (url))
    raise RuntimeError('Feedparser error with %s' % (url))
  
  maxindex = len(feed['entries']) - 1
  entry = feed['entries'][random.randint(1,maxindex)]
  
  return entry

def print_entry(entry):
  h = HTMLParser()
  try:
    link = entry.id
    title = entry.title
  except:
    log.error('cannot parse entry %s' % (entry))
    return
  print entry.title, h.unescape(entry.summary), entry.id
  
def main():
  
  default_url = 'http://feeds.feedburner.com/ThisIsWhyImBroke?format=xml'
  
  parser = ArgumentParser(description = 'Fetch random this is why im broke link')
  parser.add_argument('-u', '--url', default = default_url, help = 'specify url other than %s' % (default_url))
  args = parser.parse_args()
  
  url = args.url
  
  entry = gift_fetch(url)
  print_entry(entry)
  
  return

if __name__ == '__main__':
  sys.exit(main())
