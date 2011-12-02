import collections
import datetime
import json
from xml.etree import ElementTree as ET

import dateutil.parser

from noaa import exceptions
from noaa import geocode
from noaa import models
from noaa import utils


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
    lat, lon, address = geocode.geocode_location(location)
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

    resp = utils.open_url(FORECAST_BY_DAY_URL, params)
    tree = ET.parse(resp)

    if tree.getroot().tag == 'error':
        raise exceptions.NOAAException("Unable to retrieve forecast")

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

        if utils.any_none([min_temp_value, max_temp_value, condition]):
            continue

        temp_unit = 'C' if metric else 'F'
        min_temp = models.Temperature(min_temp_value, unit=temp_unit)
        max_temp = models.Temperature(max_temp_value, unit=temp_unit)
        datapoint = models.WeatherDataPoint(
                date, min_temp, max_temp, condition)
        new_forecast.append(datapoint)

    return new_forecast
