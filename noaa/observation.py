import os
import shutil

from noaa import geocode
from noaa import models
from noaa import stations
from noaa import utils


def observation_by_location(location, station_cache=None):
    loc = geocode.geocode_location(location)
    observation = observation_by_lat_lon(
            loc.lat, loc.lon, station_cache=station_cache)
    return observation



def observation_by_lat_lon(lat, lon, station_cache=None):
    """
    If station_cache is None, we'll fetch the station information via the
    WebService each time.

    Since this is expensive, you pass in an abspath to a file where we can
    write this data once and read from that instead.
    """
    if not station_cache:
        all_stations = stations.get_stations_from_web()
    elif not os.path.exists(station_cache):
        # Write the cache file
        resp = stations.fetch_station_data()
        with open(station_cache, "w") as f:
            shutil.copyfileobj(resp, f)

        all_stations = stations.get_stations_from_file(station_cache)
    else:
        all_stations = stations.get_stations_from_file(station_cache)

    station = stations.nearest_station(lat, lon, all_stations)
    observation = observation_by_station_id(station.station_id)
    return observation


def observation_by_station_id(station_id):
    STATION_OBSERVATIONS_URL = (
            'http://www.weather.gov/data/current_obs/%s.xml' % station_id)

    resp = utils.open_url(STATION_OBSERVATIONS_URL)
    tree = utils.parse_xml(resp)

    station = _parse_station(tree)
    observation = _parse_observation(tree, station)
    return observation


def _parse_station(tree):
    root = tree.getroot()

    lat = float(root.find("latitude").text)
    lon = float(root.find("longitude").text)
    loc_desc = root.find("location").text
    location = models.Location(lat, lon, loc_desc)

    station_id = root.find("station_id").text
    station = models.Station(station_id, location)
    return station


def _parse_observation(tree, station):
    root = tree.getroot()
    utils.print_tree(tree)

    updated_at = utils.parse_dt(root.find("observation_time_rfc822").text)

    # Oddly Norfolk, VA doesn't present temp_f and instead gives us
    # windchill_f
    try:
        temp_f = float(root.find("temp_f").text)
        temp = models.Temperature(temp_f, unit='F')
    except AttributeError:
        # FIXME(sirp): what to do here?!?
        try:
            temp_f = float(root.find("windchill_f").text)
            temp = models.Temperature(temp_f, unit='F')
        except AttributeError:
            temp = None

    try:
        relative_humidity = float(root.find("relative_humidity").text)
    except AttributeError:
        relative_humidity = None

    try:
        pressure_in = float(root.find("pressure_in").text)
        pressure = models.Pressure(pressure_in, unit='in')
    except AttributeError:
        pressure = None

    try:
        dewpoint_f = float(root.find("dewpoint_f").text)
        dewpoint = models.Temperature(dewpoint_f, unit='F')
    except AttributeError:
        dewpoint = None

    try:
        weather = root.find("weather").text
    except AttributeError:
        weather = None

    # Wind
    try:
        wind_mph = float(root.find("wind_mph").text)
        wind_speed = models.Speed(wind_mph, unit="mph")

        wind_dir = int(root.find("wind_degrees").text)
        wind_vector = models.Vector(wind_speed, wind_dir)

        wind_intensity = root.find("wind_string").text
        wind = models.Wind(wind_vector, wind_intensity)
    except AttributeError:
        wind = None

    observation = models.StationObservation(
        station, updated_at, temp, relative_humidity, pressure, dewpoint,
        weather, wind)

    return observation

if __name__ == "__main__":
    observation = observation_by_station_id('KMTN')
    print observation.temp.value
