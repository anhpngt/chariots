from typing import List

from app.types import Coord

APP_VERSION = '0.1'

# DEPOT = '-0.068372,109.362745'      # type: str
DEPOT = '1.299740,103.787517'
DEPOT_COORD = Coord(*map(float, DEPOT.split(',')))


COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'maroon', 'olive',
          'teal', 'orange', 'lime', 'cyan', 'magenta', 'mint', 'navy']  # type: List[str]


MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoicG50YTEiLCJhIjoiY2sxYzc1eHdyMDE2cTNpcW42YmNlaGFxbCJ9.vWVPDc40myK0v8x8FaQWQg'
