#!/usr/bin/env python

from argparse import ArgumentParser
import sys
import urllib2
import feedparser
import logging
import json

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def woot_fetch(url, key=None, verbose=False):
  result = []
  if not key:
    key = 'www'
  try:
    if verbose:
      log.info('Parsing url %s' % (url))
    wootfeed = feedparser.parse(url)
  except:
    log.warn('Cannot parse url %s' % (url))
    return
  try:
    if verbose:
      log.info('Searching for key: %s' % (key))
    for entry in wootfeed['entries']:
      entrykey = entry.woot_purchaseurl.split('/')[2].split('.')[0]
      if verbose:
        log.info('Found match %s' % (entry.woot_purchaseurl))
      if key == entrykey:
        result.append(entry)
  except:
    log.warn('Cannot interpret parsed result %s' % (entry))
    return
  return result

def print_result(result):
  out = []
  try:
    for entry in result:
      title = entry.title
      price = entry.woot_price
      if json.loads(entry.woot_soldout):
        purchaseurl = "Sold Out!"
      else:
        purchaseurl = entry.woot_purchaseurl
      if json.loads(entry.woot_wootoff):
        out.append("It's a woot off!")
      out.extend([title, price, purchaseurl])
      print " ".join(out)
  except:
    log.warn('Cannot find all my fields in %s' % (result))
  return
    
def main():
  
  default_url = 'http://api.woot.com/1/sales/current.rss'
  
  parser = ArgumentParser(description='fetch last item from woot feed')
  parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Be verbose.')
  parser.add_argument('-u', '--url', default=default_url, help='specify url other than {0}'.format(default_url))
  parser.add_argument('-k', '--key', default='www', help='search for tech / sport / home / etc')
  args = parser.parse_args()
  
  verbose = args.verbose
  url = args.url
  key = args.key
  
  result = woot_fetch(url, key, verbose)
  print_result(result)
  
  return

if __name__ == '__main__':
  sys.exit(main())
