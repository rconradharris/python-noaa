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


class StationObservation(object):
    def __init__(self, station, updated_at, temp):
        self.station = station
        self.updated_at = updated_at
        self.temp = temp
