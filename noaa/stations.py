import os
import shutil

import noaa.models
import noaa.utils


def nearest_stations_with_distance(lat, lon, stations, radius=10.0,
                                   units="miles"):
    """Find all stations within radius of target.

    :param lat:
    :param lon:
    :param stations: list of stations objects to scan
    :param radius:
    :param units:
    :returns: [(dist, station)]
    """
    matches = []
    for station in stations:
        s_lat = station.location.lat
        s_lon = station.location.lon
        dist = noaa.utils.earth_distance(
                s_lat, s_lon, lat, lon, dist_units=units)
        if dist <= radius:
            matches.append((dist, station))

    matches.sort()
    return matches


def nearest_station(lat, lon, stations):
    """Find single nearest station.

    :param lat:
    :param lon:
    :param stations: list of stations objects to scan
    """
    matches = nearest_stations_with_distance(lat, lon, stations)
    if matches:
        dist, station = matches[0]
    else:
        station = None

    return station


def get_stations_from_cache(filename):
    if not os.path.exists(filename):
        resp = noaa.stations.fetch_station_data()
        with open(filename, "w") as f:
            shutil.copyfileobj(resp, f)

    stations = noaa.stations.get_stations_from_file(filename)
    return stations


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
    resp = noaa.utils.open_url(STATIONS_URL)
    return resp


def _parse_stations(fileobj):
    stations = []
    tree = noaa.utils.parse_xml(fileobj)
    for station_e in tree.getroot().findall('station'):
        lat = float(station_e.find('latitude').text)
        lon = float(station_e.find('longitude').text)
        description = station_e.find('state').text
        location = noaa.models.Location(lat, lon, description)

        station_id = station_e.find('station_id').text
        station = noaa.models.Station(station_id, location)

        stations.append(station)

    return stations
