import collections
import datetime
from pprint import pprint
import urllib
from xml.etree import ElementTree as ET

import dateutil
import dateutil.parser


def print_tree(root, indent=0):
    print "%s%s%s%s" % (' ' * indent, root.tag, root.text, root.attrib)
    for child in root.getchildren():
        print_tree(child, indent + 1)


def parse_time_layouts(tree):
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

def parse_temperatures(tree):
    """Return a dictionary containing temperature information

        { 'type': { 'units': units, 
                    'time-layout': time-layout-key,
                    'values': [temp1, temp2, ...] } }
    """
    temperatures = {}
    for tmp_e in tree.getroot().getiterator(tag='temperature'):
        temp_type = tmp_e.attrib['type']

        temperature = {}
        temperature['units'] = tmp_e.attrib['units']
        temperature['time_layout'] = tmp_e.attrib['time-layout']

        values = []
        for val_e in tmp_e.getiterator(tag='value'):
            try:
                val = int(val_e.text)
            except TypeError:
                # Temp can be none if we don't have a forecast for that date
                val = None
            values.append(val)

        temperature['values'] = values
        temperatures[temp_type] = temperature

    return temperatures


def daily_forecast_by_zip(zip_code, start_date=None, num_days=7):
    """Return a daily forecast by zip code

    :param zip_code: 
    :param start_date: 
    :param num_days: 
    :param units: 
    :returns: [{'date': date, 'max_temp': max_temp, 'min_temp': min_temp}]
    """
    if not start_date:
        start_date = datetime.date.today()

    URL = "http://www.weather.gov/forecasts/xml/sample_products"\
          "/browser_interface/ndfdBrowserClientByDay.php"

    # NOTE: the order of the query-string parameters seems to matter; so,
    #   we can't use a dictionary to hold the params
    params = [("zipCodeList", zip_code),
              ("format", "24 hourly"),
              ("startDate", start_date.strftime("%Y-%m-%d")),
              ("numDays", str(num_days))]

    query_string = urllib.urlencode(params)
    url = "?".join([URL, query_string])
    resp = urllib.urlopen(url)
    tree = ET.parse(resp)

    time_layouts = parse_time_layouts(tree)
    temperatures = parse_temperatures(tree)

    def _get_dates_values(type_, temperatures, time_layouts):
        temp_info = temperatures[type_]
        time_layout_key = temp_info['time_layout']
        time_layout = time_layouts[time_layout_key]
        values = temp_info['values']
        start_dates = [st.date() for st, _ in time_layout]
        return zip(start_dates, values)

    def _group_by_date(min_data, max_data):
        grouped = collections.defaultdict(dict)
        for start_date, min_temp in min_data:
            date_key = start_date.strftime("%Y-%m-%d")
            grouped[date_key]['min_temp'] = min_temp

        for start_date, max_temp in max_data:
            date_key = start_date.strftime("%Y-%m-%d")
            grouped[date_key]['max_temp'] = max_temp

        return grouped

    min_data = _get_dates_values('minimum', temperatures, time_layouts)
    max_data = _get_dates_values('maximum', temperatures, time_layouts)
    merged = _group_by_date(min_data, max_data)

    forecast = []
    for date_key, items in sorted(merged.iteritems()):
        min_temp = items['min_temp']
        max_temp = items['max_temp']
        if min_temp is not None and max_temp is not None:
            date = datetime.datetime.strptime(date_key, "%Y-%m-%d")
            items['date'] = date
            forecast.append(items)

    return forecast

import json
forecast = daily_forecast_by_zip(78703)
dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
print json.dumps(forecast, default=dthandler)
