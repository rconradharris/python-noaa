from noaa import models
from noaa import utils


def nearest_station(lat, lon, stations):
    closest_dist = None
    closest_station = None
    for station in stations:
        s_lat = station.location.lat
        s_lon = station.location.lon
        dist = utils.earth_distance(s_lat, s_lon, lat, lon)

        if closest_dist is None or dist < closest_dist:
            closest_station = station
            closest_dist = dist

    return closest_station


def get_stations_from_web():
    resp = fetch_station_data()
    stations = _parse_stations(resp)
    return stations


def get_stations_from_file(filename):
    with open(filename) as f:
        stations = _parse_stations(f)
        return stations


def fetch_station_data():
    STATIONS_URL = "http://www.weather.gov/xml/current_obs/index.xml"
    resp = utils.open_url(STATIONS_URL)
    return resp


def _parse_stations(fileobj):
    stations = []
    tree = utils.parse_xml(fileobj)
    for station_e in tree.getroot().findall('station'):
        lat = float(station_e.find('latitude').text)
        lon = float(station_e.find('longitude').text)
        description = station_e.find('state').text
        location = models.Location(lat, lon, description)

        station_id = station_e.find('station_id').text
        station = models.Station(station_id, location)

        stations.append(station)

    return stations
