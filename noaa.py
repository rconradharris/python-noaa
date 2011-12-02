# Copyright (c) 2011 Rick Harris
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.

"""
Python bindings to grab forecast data from NOAA's web-service.
"""

import argparse
import collections
import datetime
import json
import sys
import urllib
from xml.etree import ElementTree as ET

import dateutil.parser


__version__ = "0.1"


def _any_none(L):
    return any(map(lambda x: x is None, L))


def _all_numbers(L):
    try:
        map(float, L)
        return True
    except ValueError:
        return False


class NOAAException(Exception):
    pass


class GeocodeException(NOAAException):
    pass


class Temperature(object):
    def __init__(self, value, unit):
        self.value = value
        self.unit = unit

    @property
    def farenheit(self):
        if self.unit == "F":
            return self.value
        return (9.0 / 5) * self.value + 32

    @property
    def celsius(self):
        if self.unit == "C":
            return self.value
        return (5.0 / 9) * (self.value - 32)


class WeatherDataPoint(object):
    def __init__(self, date, min_temp, max_temp, conditions):
        self.date = date
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.conditions = conditions


def print_tree(tree, indent=4):
    def print_elem(elem, level):
        print " " * (indent * level),
        print 'tag="%s"' % elem.tag,
        print 'text="%s"' % elem.text.strip() if elem.text is not None else "",
        print 'attrib=%s' % elem.attrib
        for child in elem.getchildren():
            print_elem(child, level + 1)
    print_elem(tree.getroot(), 0)


def _open_url(url, params=None):
    if params:
        query_string = urllib.urlencode(params)
        url = "?".join([url, query_string])

    resp = urllib.urlopen(url)
    return resp


def _geocode_location(location):
    GEOCODE_URL = "http://maps.google.com/maps/geo"
    params = [('q', location),
              ('sensor', 'false'),
              ('output', 'json')]

    resp = _open_url(GEOCODE_URL, params)
    data = json.loads(resp.read())

    if data['Status']['code'] != 200:
        raise GeocodeException('Unable to geocode this location')

    best_match = data['Placemark'][0]
    address = best_match['address']
    lon, lat, _ = best_match['Point']['coordinates']
    return lat, lon, address


def _parse_time_layouts(tree):
    """Return a dictionary containing the time-layouts

    A time-layout looks like:

        { 'time-layout-key': [(start-time, end-time), ...] }
    """
    parse_dt = dateutil.parser.parse
    time_layouts = {}
    for tl_elem in tree.getroot().getiterator(tag="time-layout"):
        start_times = []
        end_times = []
        for tl_child in tl_elem.getchildren():
            if tl_child.tag == "layout-key":
                key = tl_child.text
            elif tl_child.tag == "start-valid-time":
                dt = parse_dt(tl_child.text)
                start_times.append(dt)
            elif tl_child.tag == "end-valid-time":
                dt = parse_dt(tl_child.text)
                end_times.append(dt)

        time_layouts[key] = zip(start_times, end_times)

    return time_layouts


def _parse_temperatures_for_type(tree, temp_type):
    for tmp_e in tree.getroot().getiterator(tag='temperature'):
        if tmp_e.attrib['type'] != temp_type:
            continue
        values = []
        for val_e in tmp_e.getiterator(tag='value'):
            try:
                val = int(val_e.text)
            except TypeError:
                # Temp can be none if we don't have a forecast for that
                # date
                val = None
            values.append(val)

        time_layout_key = tmp_e.attrib['time-layout']
        return time_layout_key, values

    raise Exception("temp type '%s' not found in data")


def _parse_conditions(tree):
    for weather_e in tree.getroot().getiterator(tag='weather'):
        values = []
        for condition_e in weather_e.getiterator(tag='weather-conditions'):
            value = condition_e.attrib.get('weather-summary')
            values.append(value)

        time_layout_key = weather_e.attrib['time-layout']
        return time_layout_key, values


def daily_forecast_by_zip_code(zip_code, start_date=None, num_days=6,
                              metric=False):
    """Return a daily forecast by zip code.

    :param zip_code:
    :param start_date:
    :param num_days:
    :returns: [WeatherDataPoint() ...]
    """
    location_info = [("zipCodeList", zip_code)]
    return _daily_forecast_from_location_info(
            location_info, start_date=start_date, num_days=num_days,
            metric=metric)


def daily_forecast_by_lat_lon(lat, lon, start_date=None, num_days=6,
                              metric=False):
    """Return a daily forecast by lat lon.

    :param lat:
    :param lon:
    :param start_date:
    :param num_days:
    :returns: [WeatherDataPoint() ...]
    """
    location_info = [("lat", lat), ("lon", lon)]
    return _daily_forecast_from_location_info(
            location_info, start_date=start_date, num_days=num_days,
            metric=metric)


def daily_forecast_by_location(location, start_date=None, num_days=6,
                               metric=False):
    lat, lon, address = _geocode_location(location)
    return address, daily_forecast_by_lat_lon(
            lat, lon, start_date=start_date, num_days=num_days, metric=metric)


def _daily_forecast_from_location_info(location_info, start_date=None,
                                       num_days=6, metric=False):
    if not start_date:
        start_date = datetime.date.today()

    unit = "m" if metric else "e"

    # NOTE: the order of the query-string parameters seems to matter; so,
    # we can't use a dictionary to hold the params
    params = location_info + [("format", "24 hourly"),
                              ("startDate", start_date.strftime("%Y-%m-%d")),
                              ("numDays", str(num_days)),
                              ("Unit", unit)]

    FORECAST_BY_DAY_URL = ("http://www.weather.gov/forecasts/xml"
                           "/sample_products/browser_interface"
                           "/ndfdBrowserClientByDay.php")

    resp = _open_url(FORECAST_BY_DAY_URL, params)
    tree = ET.parse(resp)

    if tree.getroot().tag == 'error':
        raise NOAAException("Unable to retrieve forecast")

    time_layouts = _parse_time_layouts(tree)
    min_temp_tlk, min_temps = _parse_temperatures_for_type(tree, 'minimum')
    max_temp_tlk, max_temps = _parse_temperatures_for_type(tree, 'maximum')
    conditions_tlk, conditions = _parse_conditions(tree)

    # Time layout keys have to match for us to sequence and group by them
    assert (min_temp_tlk == max_temp_tlk == conditions_tlk)

    time_layout_key = min_temp_tlk
    time_layout = time_layouts[time_layout_key]
    dates = [dt.date() for dt, _ in time_layout]

    new_forecast = []
    for date, min_temp_value, max_temp_value, condition in zip(
            dates, min_temps, max_temps, conditions):

        if _any_none([min_temp_value, max_temp_value, condition]):
            continue

        temp_unit = 'C' if metric else 'F'
        min_temp = Temperature(min_temp_value, unit=temp_unit)
        max_temp = Temperature(max_temp_value, unit=temp_unit)
        datapoint = WeatherDataPoint(date, min_temp, max_temp, condition)
        new_forecast.append(datapoint)

    return new_forecast


def main():
    def colorize(text, color, stream=sys.stdout):
        if not stream.isatty():
            return text
        if color == "default":
            return text
        COLORS = {"black": 30,
                  "red": 31,
                  "green": 32,
                  "yellow": 33,
                  "blue": 34,
                  "magenta": 35,
                  "cyan": 36,
                  "white": 37}
        color_code = COLORS[color]
        return "\x1b[%(color_code)s;1m%(text)s\x1b[0m" % locals()

    def simple_temp_graph(temp):
        scale = 0.5 if temp.unit == "F" else 1.0
        value = temp.value
        if value is None:
            return ''
        char = '+' if value >= 0 else '-'
        scaled_temp = int(abs(value * scale))
        return colorize(char * scaled_temp, "white")

    def format_temp(temp, padding=5):
        value = temp.value
        if value is None:
            return 'N/A'.rjust(padding)

        def temp_color(value_f):
            if value_f >= 90:
                return "red"      # hot
            elif value_f >= 68:
                return "yellow"   # warm
            elif value_f >= 55:
                return "default"    # nice
            elif value_f >= 32:
                return "blue"     # cold
            elif value_f > 0:
                return "cyan"     # freezing
            else:
                return "magenta"  # below zero

        color = temp_color(temp.farenheit)
        return (colorize(str(value).rjust(padding), color) + ' ' + temp.unit)

    def format_conditions(conditions, padding=30):
        if conditions is None:
            return 'N/A'.ljust(padding)

        def conditions_color(conditions):
            if 'Sunny' in conditions:
                return 'yellow'
            elif 'Rain' in conditions:
                return 'cyan'
            elif 'Drizzle' in conditions:
                return 'green'
            elif 'Thunderstorms' in conditions:
                return 'red'
            elif 'Cold' in conditions:
                return 'blue'
            else:
                return "default"

        color = conditions_color(conditions)
        return colorize(conditions.ljust(padding), color)

    def make_parser():
        parser = argparse.ArgumentParser()
        parser.add_argument('location', nargs="+")
        parser.add_argument('-m', '--metric', action="store_true",
                            help="use Celsius for temperatures")
        return parser

    parser = make_parser()
    args = parser.parse_args()
    metric = args.metric

    if not _all_numbers(args.location):
        # Args not being all numbers implies we were passed a string location
        location = " ".join(args.location)
        try:
            address, forecast = daily_forecast_by_location(
                    location, metric=metric)
        except NOAAException as e:
            print >> sys.stderr, "Error: %s" % e
            sys.exit(1)
        pretty_location = address
    elif len(args.location) == 1:
        # All numbers with one argument implies zip code
        zip_code = "".join(args.location)
        pretty_location = zip_code

        try:
            forecast = daily_forecast_by_zip_code(zip_code, metric=metric)
        except NOAAException as e:
            print >> sys.stderr, "Error: %s" % e
            sys.exit(1)
    elif len(args.location) == 2:
        # 3 args that are all numbers implies lat lon coordinates
        lat, lon = args.location
        pretty_location = ', '.join([lat, lon])

        try:
            forecast = daily_forecast_by_lat_lon(lat, lon, metric=metric)
        except NOAAException as e:
            print >> sys.stderr, "Error: %s" % e
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    print "Forecast for %s" % pretty_location
    for datapoint in forecast:
        print datapoint.date.strftime('%a'),
        print format_conditions(datapoint.conditions),
        print format_temp(datapoint.min_temp),
        print format_temp(datapoint.max_temp),
        print simple_temp_graph(datapoint.max_temp)


if __name__ == "__main__":
    main()
