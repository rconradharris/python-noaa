import os
import shutil

import noaa.exceptions
import noaa.geocode
import noaa.models
import noaa.stations
import noaa.utils


def observation_by_location(location, station_cache=None):
    loc = noaa.geocode.geocode_location(location)
    observation = observation_by_lat_lon(
            loc.lat, loc.lon, station_cache=station_cache)
    return observation


def observation_by_lat_lon(lat, lon, station_cache=None, radius=10.0,
                           units="miles"):
    """
    If station_cache is None, we'll fetch the station information via the
    WebService each time.

    Since this is expensive, you pass in an abspath to a file where we can
    write this data once and read from that instead.
    """
    if not station_cache:
        all_stations = noaa.stations.get_stations_from_web()
    elif not os.path.exists(station_cache):
        # Write the cache file
        resp = noaa.stations.fetch_station_data()
        with open(station_cache, "w") as f:
            shutil.copyfileobj(resp, f)

        all_stations = noaa.stations.get_stations_from_file(station_cache)
    else:
        all_stations = noaa.stations.get_stations_from_file(station_cache)

    #station = noaa.stations.nearest_station(lat, lon, all_stations)
    #observation = observation_by_station_id(station.station_id)
    #return observation

    matches = noaa.stations.nearest_stations_with_distance(
            lat, lon, all_stations, radius=radius, units=units)

    for dist, station in matches:
        try:
            return observation_by_station_id(station.station_id)
        except noaa.exceptions.StationObservationMissingInfo, e:
            print e
            continue

    raise noaa.exceptions.ValidStationObservationNotFound(
            "Could not find a valid station observation within %(radius)s"
            " %(units)s of (%(lat)s, %(lon)s)." % locals())



def observation_by_station_id(station_id):
    """
    Unfortunately not all NOAA stations return the same metrics: one station
    may return temp_f while another may return windchill_f.

    To work around this, we scan all stations within a radius of the target
    and return the observation (if any) that has the data we want.
    """
    STATION_OBSERVATIONS_URL = (
            'http://www.weather.gov/data/current_obs/%s.xml' % station_id)

    resp = noaa.utils.open_url(STATION_OBSERVATIONS_URL)
    tree = noaa.utils.parse_xml(resp)

    station = _parse_station(tree)
    observation = _parse_observation(tree, station)
    return observation


def _parse_station(tree):
    root = tree.getroot()

    lat = float(root.find("latitude").text)
    lon = float(root.find("longitude").text)
    loc_desc = root.find("location").text
    location = noaa.models.Location(lat, lon, loc_desc)

    station_id = root.find("station_id").text
    station = noaa.models.Station(station_id, location)
    return station


def _find_elem(tree, tag, required=False):
    elem = tree.getroot().find(tag)
    if elem is not None or not required:
        return elem
    else:
        raise noaa.exceptions.StationObservationMissingInfo(
            "StationObservation is missing '%s'" % tag)


def _parse_observation(tree, station):
    root = tree.getroot()
    noaa.utils.print_tree(tree)

    updated_at = noaa.utils.parse_dt(root.find("observation_time_rfc822").text)

    temp_e = root.find("temp_f")
    if temp_e is None:
        raise noaa.exceptions.StationObservationMissingInfo(
            "StationObservation is missing 'temp_f'")
    else:
        temp = noaa.models.Temperature(float(temp_e.text), unit='F')

    observation = noaa.models.StationObservation(station, updated_at, temp)
    return observation

if __name__ == "__main__":
    observation = observation_by_station_id('KMTN')
    print observation.temp.value
