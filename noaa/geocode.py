import json

from noaa import exceptions
from noaa import models
from noaa import utils


def geocode_location(location, api_key=None):
    """Use Google to geocode a location string.

    For high-volume traffic, you will need to specify an API-key.
    """
    GEOCODE_URL = "http://maps.googleapis.com/maps/api/geocode/json"
    params = [('address', location)]

    if api_key:
        params += [('key', api_key)]

    resp = utils.open_url(GEOCODE_URL, params)
    data = json.loads(resp.read().decode())

    if data['status'] != 'OK':
        raise exceptions.GeocodeException('Unable to geocode this location')

    address = data['results'][0]['formatted_address']
    lon = data['results'][0]['geometry']['location']['lng']
    lat = data['results'][0]['geometry']['location']['lat']

    location = models.Location(lat, lon, address)
    return location
