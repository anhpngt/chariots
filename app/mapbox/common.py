import os
from typing import Optional

import requests

from app.constants import APP_VERSION
from app.constants import MAPBOX_ACCESS_TOKEN

ALLOWED_MAPBOX_PROFILE = {
    'mapbox/driving-traffic',
    'mapbox/driving',
    'mapbox/walking',
    'mapbox/cycling'
}


def _Session(access_token: Optional[str] = None) -> requests.Session:
    access_token = (
        access_token or
        os.environ.get('MAPBOX_ACCESS_TOKEN') or
        MAPBOX_ACCESS_TOKEN)

    session = requests.Session()
    session.params.update(access_token=access_token)
    session.headers.update({
        'User-Agent': f'flask-chariots/v{APP_VERSION}'
    })
    return session


class Service:
    MAPBOX_DEFAULT_HOST = 'https://api.mapbox.com'

    def __init__(self,
                 access_token: Optional[str] = None,
                 host: Optional[str] = None):
        self.session = _Session(access_token)
        self.host = host or self.MAPBOX_DEFAULT_HOST

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()

    def response_handler(self, response: requests.Response) -> None:
        if response.status_code == 200:
            return
        else:
            print('Warning: HTTP request failed')
