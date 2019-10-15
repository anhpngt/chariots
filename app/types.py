import numpy as np


class Coord:
    EARTH_RADIUS = 6373.0

    def __init__(self, lat: float, lng: float) -> None:
        self.lat = lat          # type: float
        self.lng = lng          # type: float

    def __repr__(self):
        return f'[{self.lat};{self.lng}]'

    @property
    def lnglat(self):
        return f'{format_float(self.lng)},{format_float(self.lat)}'

    @property
    def latlng(self):
        return f'{format_float(self.lat)},{format_float(self.lng)}'

    def utm_dist(self, other: 'Coord') -> int:
        dlat = other.lat - self.lat
        dlng = other.lng - self.lng
        a = np.sin(dlat / 2) ** 2 + \
            np.cos(self.lat) * np.cos(other.lat) * np.sin(dlng / 2) ** 2

        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distance = int(Coord.EARTH_RADIUS * c * 1000)
        return distance


# Referenced from googlemaps.convert.format_float
def format_float(arg):
    """Formats a float value to be as short as possible.

    Truncates float to 8 decimal places and trims extraneous
    trailing zeros and period to give API args the best
    possible chance of fitting within 2000 char URL length
    restrictions.

    For example:

    format_float(40) -> "40"
    format_float(40.0) -> "40"
    format_float(40.1) -> "40.1"
    format_float(40.001) -> "40.001"
    format_float(40.0010) -> "40.001"
    format_float(40.000000001) -> "40"
    format_float(40.000000009) -> "40.00000001"

    :param arg: The lat or lng float.
    :type arg: float

    :rtype: string
    """
    return ("%.8f" % float(arg)).rstrip("0").rstrip(".")
