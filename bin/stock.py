#!/usr/bin/env python
'''
fetches stock info from google
'''
from argparse import ArgumentParser
import sys
import urllib2
import json
from pprint import pprint as pp

def fetchstockinfo(apiurl, search):
  jsondata = {}
  try:
    url = apiurl + search
    req = urllib2.Request(url)
    res = urllib2.urlopen(req)
    data = res.read()
    data = data.replace('\n','').split('//')[1].strip()
    jsondata = json.loads(data)
  except:
    pass
  return jsondata

def print_result(result):
  if result == {}:
    print "I don't know that symbol.."
  printthis = "{0}:{1} {2} :: {3} {4} ({5}%)"
  for entry in result:
    try:
      print printthis.format(entry['e'], entry['t'], entry['lt'], entry['l'], entry['c'], entry['cp'])
    except:
      print "I can't parse the result."

def main():
  parser = ArgumentParser(description='fetches stock info from google')
  parser.add_argument('--api-url', default='http://www.google.com/finance/info?q=', help='Specify another api url')
  parser.add_argument('searchstring', \
                    metavar='searchstring', nargs='+', \
                    type=str, help='stock symbol to search for')
  args = parser.parse_args()
  
  searches = args.searchstring
  apiurl = args.api_url
  
  for search in searches:
    result = fetchstockinfo(apiurl, search)
    print_result(result)

if __name__ == '__main__':
  sys.exit(main())
        
  
