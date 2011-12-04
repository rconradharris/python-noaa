class Dimension(object):
    def __init__(self, value, unit):
        self.value = value
        self.unit = unit


class Speed(Dimension):
    @property
    def kph(self):
        #TODO: write this
        pass

    @property
    def mph(self):
        #TODO: write this
        pass


class Vector(object):
    def __init__(self, speed, direction):
        self.speed = speed
        self.direction = direction


class Location(object):
    def __init__(self, lat, lon, description):
        self.lat = lat
        self.lon = lon
        self.description = description


class Pressure(Dimension):
    @property
    def inches(self):
        #TODO: write this
        pass

    @property
    def millibars(self):
        #TODO: write this
        pass


class Temperature(Dimension):
    @property
    def farenheit(self):
        if self.unit == "F":
            return self.value
        return (9.0 / 5) * self.value + 32

    @property
    def celsius(self):
        if self.unit == "C":
            return self.value
        return (5.0 / 9) * (self.value - 32)


class Wind(object):
    def __init__(self, vector, intensity):
        self.vector = vector
        self.intensity = intensity


class ForecastedCondition(object):
    def __init__(self, date, min_temp, max_temp, conditions):
        self.date = date
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.conditions = conditions


class Station(object):
    def __init__(self, station_id, location):
        self.station_id = station_id
        self.location = location


class Observation(object):
    """
    NOAA's stations may return different observation parameters. Station
    identification and pickup information appears to be consistent, but
    nothing weather related can be assumed to be present.

    If you want the temperture for a location, you must search all stations
    nearby for a station that provides the `temp_f` parameter.
    """
    def __init__(self, updated_at, temp):
        self.updated_at = updated_at
        self.temp = temp


class StationObservation(object):
    def __init__(self, station, observation):
        self.station = station
        self.observation = observation
