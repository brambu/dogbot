#!/usr/bin/env python

#!/usr/bin/env python

from argparse import ArgumentParser
import sys
import logging
import urllib
import urllib2
import json
from pprint import pprint as pp

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def directions(apiurl, mapsurl, src, dst):
  result = {}
  apidict = {}
  mapsdict = {}
  apidict['origin'] = src
  apidict['destination'] = dst
  apidict['sensor'] = 'false'
  mapsdict['saddr'] = src
  mapsdict['daddr'] = dst
  result['apiurl'] = apiurl + '?' + urllib.urlencode(apidict)
  result['mapsurl'] = mapsurl + '?' + urllib.urlencode(mapsdict)
  
  req = urllib2.Request(result['apiurl'])
  response = urllib2.urlopen(req)
  directionsdict = json.load(response)
  
  route = directionsdict['routes'][0]
  leg = route['legs'][0]
  
  result['distance'] = leg['distance']['text']
  result['time'] = leg['duration']['text']
  result['start'] = leg['start_address']
  result['end'] = leg['end_address']
  
  return result

def print_result(result):
  print "Directions from {start} to {end} - {distance} in {time} - {mapsurl}".format(**result)
  

def main():
  
  parser = ArgumentParser(description = 'some script')
  parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Be verbose.')
  parser.add_argument('query', nargs='+', help='from __ to __')
  args = parser.parse_args()
  
  #http://maps.googleapis.com/maps/api/directions/json?origin=94041&destination=94089&sensor=false
  #https://maps.google.com/maps?saddr=94041&daddr=94089
  query = args.query
  verbose = args.verbose
  
  fromlist = []
  tolist = []
  onfrom = False
  onto = False
  for i in query:
    if 'from' in i.lower():
      onfrom = True
      onto = False
    if 'to' in i.lower():
      onfrom = False
      onto = True
    if onfrom:
      if i != 'from':
        fromlist.append(i)
    if onto:
      if i != 'to':
        tolist.append(i)
  
  src = " ".join(fromlist)
  dst = " ".join(tolist)
  
  apiurl = 'http://maps.googleapis.com/maps/api/directions/json'
  mapsurl = 'https://maps.google.com/maps'
  
  result = directions(apiurl, mapsurl, src, dst)
  print_result(result)
  
  return

if __name__ == '__main__':
  sys.exit(main())
