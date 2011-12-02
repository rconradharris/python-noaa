class Temperature(object):
    def __init__(self, value, unit):
        self.value = value
        self.unit = unit

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


class DailyWeatherDataPoint(object):
    def __init__(self, date, min_temp, max_temp, conditions):
        self.date = date
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.conditions = conditions
