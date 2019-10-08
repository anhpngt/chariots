import numpy as np


class Coord:
    EARTH_RADIUS = 6373.0

    def __init__(self, lat: float, lng: float) -> None:
        self.lat = lat          # type: float
        self.lng = lng          # type: float

    @property
    def lnglat(self):
        return '{},{}'.format(self.lng, self.lat)

    def utm_dist(self, other: 'Coord') -> int:
        dlat = other.lat - self.lat
        dlng = other.lng - self.lng
        a = np.sin(dlat / 2) ** 2 + \
            np.cos(self.lat) * np.cos(other.lat) * np.sin(dlng / 2) ** 2

        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distance = int(Coord.EARTH_RADIUS * c * 1000)
        return distance
