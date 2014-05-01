#!/usr/bin/env python

from argparse import ArgumentParser
import pywapi
import sys

ctof = lambda x: int(((float(x) * 9.0 ) / 5.0 ) + 32.0)
ftoc = lambda x: int((float(x)  - 32.0) / 1.8 )
kmhtomph = lambda x: int(float(x) / 1.609344)

def calc_heat_index(t, h):
    return -42.379 + (2.04901523 * t) +\
           (10.14333127 * h) - (0.22475541 * t * h) -\
           (6.83783 * (10**-3) * (t**2)) -\
           (5.481717 * (10**-2) * (h**2)) +\
           (1.22874 * (10**-3) * (t**2) * h) +\
           (8.5282 * (10**-4) * t * (h**2)) -\
           (1.99 * ( 10**-6) * (t**2) * (h**2))

def weather_for_zip(zipcode):
    try:
        result = pywapi.get_weather_from_yahoo(zipcode)
    except:
        result = None
    return result

def print_result(result, mode='summer'):
    #from pprint import pprint as pp
    #pp(result)
    #import pdb; pdb.set_trace()
    try:
        title = result['condition']['title']
        text = result['condition']['text']
        tempc = result['condition']['temp']
        high = result['forecasts'][0]['high']
        low = result['forecasts'][0]['low']
        forecast = result['forecasts'][0]['text']
        windchillc = result['wind']['chill']
        windspeedkm = result['wind']['speed']
        humidity = result['atmosphere']['humidity']
        heatindex = int(calc_heat_index(float(ctof(tempc)), float(humidity)))
        if mode == 'winter':
            printthis = "{0} Currently {1} {2}F/{3}C  "+\
                        "Forecast: {4} (High {5}F/{6}C - Low {7}F/{8}C) "+\
                        "[Wind: chill {9}F/{10}C speed {11}mph/{12}kmh]"
            printthis = printthis.format(title, text, ctof(tempc), tempc,
                                        forecast, ctof(high), high, ctof(low), low,
                                        ctof(windchillc), windchillc, kmhtomph(windspeedkm), int(float(windspeedkm)))
        if mode == 'summer':
            printthis = "{0} Currently {1} {2}F/{3}C "+\
                        "Forecast: {4} (High {5}F/{6}C - Low {7}F/{8}C) "+\
                        "[Humidity: {9}% - Heat Index: {10}F/{11}C - Wind: {12}mph/{13}kmh]"
            printthis = printthis.format(title, text, ctof(tempc), tempc,
                                        forecast, ctof(high), high, ctof(low), low,
                                        humidity, heatindex, ftoc(heatindex), kmhtomph(windspeedkm), int(float(windspeedkm)))
    except:
        printthis = 'Not sure.'

    print printthis
    return

def main():

    parser = ArgumentParser(description='weather fetch by zip')
    parser.add_argument('-z','--zip',required=True,help='zip code')
    parser.add_argument('-m', '--mode', default='summer', help='summer or winter mode' )
    args = parser.parse_args()

    zipcode = args.zip
    mode = args.mode
    result = weather_for_zip(zipcode)
    if result:
        print_result(result, mode)
    else:
        print "No results."

    return

if __name__ == '__main__':
    sys.exit(main())
