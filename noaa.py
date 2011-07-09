from xml.etree import ElementTree as ET
from pprint import pprint
import urllib

import dateutil
import dateutil.parser


URL = "http://www.weather.gov/forecasts/xml/sample_products/"\
      "browser_interface/ndfdXMLclient.php"

params = {
    "lat": "38.99",
    "lon": "-77.01",
    "product": "time-series", 
    "begin": "2004-01-01T00:00:00", 
    "end": "2013-04-20T00:00:00", 
    "maxt": "maxt", 
    "mint": "mint"
}

def print_tree(root, indent=0):
    print "%s%s%s%s" % (' ' * indent, root.tag, root.text, root.attrib)
    for child in root.getchildren():
        print_tree(child, indent + 1)


query_string = urllib.urlencode(params)
url = "?".join([URL, query_string])
resp = urllib.urlopen(url)
tree = ET.parse(resp)

def parse_time_layout(tree):
    """Return a dictionary containing the time-layouts

    A time-layout looks like:

        { 'time-layout-key': [(start-time, end-time), ...] }
    """
    parse_dt = dateutil.parser.parse
    time_layout = {}
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

        time_layout[key] = zip(start_times, end_times)

    return time_layout

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
            val = int(val_e.text)
            values.append(val)

        temperature['values'] = values
        temperatures[temp_type] = temperature

    return temperatures

pprint(parse_time_layout(tree))
pprint(parse_temperatures(tree))
