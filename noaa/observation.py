import noaa.exceptions
import noaa.geocode
import noaa.models
import noaa.stations
import noaa.utils


def nearby_observations_for_location(location, stations):
    loc = noaa.geocode.geocode_location(location)
    observations = nearby_observations_for_lat_lon(loc.lat, loc.lon, stations)
    return observations


def nearby_observations_for_lat_lon(lat, lon, stations, radius=10.0,
                                   units="miles"):
    observations = []
    for dist, station in noaa.stations.nearest_stations_with_distance(
            lat, lon, stations, radius=radius, units=units):
        observation = observation_by_station_id(station.station_id)
        observations.append(observation)

    return observations


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


def _parse_observation(tree, station):
    root = tree.getroot()
    noaa.utils.print_tree(tree)

    updated_at = noaa.utils.parse_dt(root.find("observation_time_rfc822").text)

    temp_e = root.find("temp_f")
    if temp_e is None:
        temp = None
    else:
        temp = noaa.models.Temperature(float(temp_e.text), unit='F')

    observation = noaa.models.StationObservation(station, updated_at, temp)
    return observation

if __name__ == "__main__":
    observation = observation_by_station_id('KMTN')
    print observation.temp.value
