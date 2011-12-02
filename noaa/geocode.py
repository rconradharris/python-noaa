import json

from noaa import exceptions
from noaa import utils


def geocode_location(location, api_key=None):
    """Use Google to geocode a location string.

    For high-volume traffic, you will need to specify an API-key.
    """
    GEOCODE_URL = "http://maps.google.com/maps/geo"
    params = [('q', location),
              ('sensor', 'false'),
              ('output', 'json')]

    if api_key:
        params += [('key', api_key)]

    resp = utils.open_url(GEOCODE_URL, params)
    data = json.loads(resp.read())

    if data['Status']['code'] != 200:
        raise exceptions.GeocodeException('Unable to geocode this location')

    best_match = data['Placemark'][0]
    address = best_match['address']
    lon, lat, _ = best_match['Point']['coordinates']
    return lat, lon, address
