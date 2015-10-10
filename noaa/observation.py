import copy

import noaa.exceptions
import noaa.geocode
import noaa.models
import noaa.stations
import noaa.utils


def compiled_observation_for_location(location, stations, radius=10.0,
                                      units="miles"):
    loc = noaa.geocode.geocode_location(location)
    compiled_observation = compiled_observation_for_lat_lon(
            loc.lat, loc.lon, stations, radius=radius, units=units)
    return compiled_observation


def compiled_observation_for_lat_lon(lat, lon, stations, radius=10.0,
                                     units="miles"):
    """Since some NOAA stations may not provide all of the data, this function
    attempts to search nearby Stations to create a single Observation
    that contains as much information as possible.
    """
    compiled_observation = None
    for station_observation in nearby_station_observations_for_lat_lon(
            lat, lon, stations, radius=radius, units=units):

        if not compiled_observation:
            compiled_observation = copy.copy(station_observation.observation)

        if not noaa.utils.any_none(list(compiled_observation.__dict__.values())):
            # If all the values are filled in, break out of loop
            break

        for attr, compiled_value in list(compiled_observation.__dict__.items()):
            if compiled_value is None:
                station_value = getattr(station_observation.observation, attr)
                setattr(compiled_observation, attr, station_value)

    return compiled_observation


def nearby_station_observations_for_location(location, stations):
    loc = noaa.geocode.geocode_location(location)
    station_observations = nearby_station_observations_for_lat_lon(
            loc.lat, loc.lon, stations)
    return station_observations


def nearby_station_observations_for_lat_lon(lat, lon, stations, radius=10.0,
                                            units="miles"):
    station_observations = []
    for dist, station in noaa.stations.nearest_stations_with_distance(
            lat, lon, stations, radius=radius, units=units):
        station_observation = station_observation_by_station_id(
                station.station_id)
        station_observations.append(station_observation)

    return station_observations


def station_observation_by_station_id(station_id):
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
    observation = _parse_observation(tree)
    station_observation = noaa.models.StationObservation(station, observation)
    return station_observation


def _parse_station(tree):
    root = tree.getroot()

    lat = float(root.find("latitude").text)
    lon = float(root.find("longitude").text)
    loc_desc = root.find("location").text
    location = noaa.models.Location(lat, lon, loc_desc)

    station_id = root.find("station_id").text
    station = noaa.models.Station(station_id, location)
    return station


def _parse_observation(tree):
    root = tree.getroot()
    updated_at = noaa.utils.parse_dt(root.find("observation_time_rfc822").text)

    temp_e = root.find("temp_f")
    if temp_e is None:
        temp = None
    else:
        temp = noaa.models.Temperature(float(temp_e.text), unit='F')

    observation = noaa.models.Observation(updated_at, temp)
    return observation
