class NOAAException(Exception):
    pass


class GeocodeException(NOAAException):
    pass


class StationObservationMissingInfo(NOAAException):
    pass


class ValidStationObservationNotFound(NOAAException):
    pass
