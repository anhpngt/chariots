from typing import List
from typing import Optional

import requests

from app.mapbox.common import ALLOWED_MAPBOX_PROFILE
from app.mapbox.common import Service
from app.types import Coord


class MatrixService(Service):
    ENDPOINT = 'directions-matrix'
    VERSION = 'v1'
    REQUEST_LIMIT = 60      # number per minute limitation

    def __init__(self,
                 access_token: Optional[str] = None,
                 host: Optional[str] = None):
        super().__init__(access_token, host)
        self.request_counter = 0            # type: int

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    @property
    def baseuri(self):
        return f'{self.host}/{self.ENDPOINT}/{self.VERSION}'

    def request(self,
                coordinates: List[Coord],
                profile: str = 'mapbox/driving',
                **kwargs) -> List[List[float]]:
        assert 2 <= len(coordinates) <= 25, 'Invalid number of coordinates'
        assert profile in ALLOWED_MAPBOX_PROFILE, 'Invalid profile'

        annotations = kwargs.get('annotations') or 'duration,distance'
        coords_url_format = ';'.join([c.lnglat for c in coordinates])
        url = f'{self.baseuri}/{profile}/{coords_url_format}' \
              f'?annotations={annotations}'
        response = self.session.get(url, timeout=30)
        self.request_counter += 1
        self.response_handler(response)

        return self._parse_response(response)

    def _parse_response(self, response: requests.Response) -> List[List[float]]:
        jsonbody = response.json()
        return jsonbody['distances']
