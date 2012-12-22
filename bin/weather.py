#!/usr/bin/env python

from argparse import ArgumentParser
import pywapi
import sys

ctof = lambda x: int(((float(x) * 9.0 ) / 5.0 ) + 32.0)
kmhtomph = lambda x: int(float(x) / 1.609344)

def weather_for_zip(zipcode):
    try:
        result = pywapi.get_weather_from_yahoo(zipcode)
    except:
        result = None
    return result

def print_result(result):
    try:
        title = result['condition']['title']
        text = result['condition']['text']
        tempc = result['condition']['temp']
        high = result['forecasts'][0]['high']
        low = result['forecasts'][0]['low']
        forecast = result['forecasts'][0]['text']
        windchillc = result['wind']['chill']
        windspeedkm = result['wind']['speed']
        printthis = "{0} Currently {1} {2}F/{3}C  "+\
                    "Forecast: {4} (High {5}F/{6}C - Low {7}F/{8}C) "+\
                    "Wind: chill {9}F/{10}C speed {11}mph/{12}kmh"
        printthis = printthis.format(title, text, ctof(tempc), tempc,
                                     forecast, ctof(high), high, ctof(low), low,
                                     ctof(windchillc), windchillc, kmhtomph(windspeedkm), int(float(windspeedkm)))
    except:
        printthis = 'Not sure.'
        
    print printthis
    return

def main():
    
    parser = ArgumentParser(description='weather fetch by zip')
    parser.add_argument('-z','--zip',required=True,help='zip code')
    args = parser.parse_args()
    
    zipcode = args.zip
    
    result = weather_for_zip(zipcode)
    if result:
        print_result(result)
    else:
        print "No results."

    return

if __name__ == '__main__':
    sys.exit(main())