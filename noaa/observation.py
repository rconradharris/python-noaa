from noaa import models
from noaa import utils


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

    updated_at = utils.parse_dt(root.find("observation_time_rfc822").text)

    temp_f = float(root.find("temp_f").text)
    temp = models.Temperature(temp_f, unit='F')

    relative_humidity = float(root.find("relative_humidity").text)

    pressure_in = float(root.find("pressure_in").text)
    pressure = models.Pressure(pressure_in, unit='in')

    dewpoint_f = float(root.find("dewpoint_f").text)
    dewpoint = models.Temperature(dewpoint_f, unit='F')

    weather = root.find("weather").text

    # Wind
    wind_mph = float(root.find("wind_mph").text)
    wind_speed = models.Speed(wind_mph, unit="mph")

    wind_dir = int(root.find("wind_degrees").text)
    wind_vector = models.Vector(wind_speed, wind_dir)

    wind_intensity = root.find("wind_string").text
    wind = models.Wind(wind_vector, wind_intensity)

    observation = models.StationObseration(
        station, updated_at, temp, relative_humidity, pressure, dewpoint,
         weather, wind)

    return observation

if __name__ == "__main__":
    observation = observation_by_station_id('KMTN')
    print observation.temp.value
