from typing import List
from typing import Optional

import numpy as np
from flask import current_app
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2

from app.constants import DEPOT_COORD
from app.database.models import Order, DistanceMatrix
from app.database.models import Vehicle
from app.mapbox import MatrixService
from app.plugins import gmaps
from app.types import Coord


class DataModel:
    def __init__(self):
        # Whether model data has been added (thus solve() can be called)
        self._initialized = False

        # For data model, contains all addresses of orders (as Coord).
        # The first address in the list is the depot
        self.addresses = [DEPOT_COORD]      # type: List[Coord]

        # Demands (or capacity constraints) for the addresses.
        self.demands = [0]                  # type: List[int]

        # Index of the depot in the lists above
        self.depot = 0                      # type: int

        # Maximum capacity of the vehicles
        self.vehicle_capacities = []        # type: List[int]

        # Distance matrix between the addresses, to be filled from
        # database or from mapbox
        self.distance_matrix = None         # type: Optional[np.ndarray]

        self.order_list = []                # type: List[Order]
        self.vehicle_list = []              # type: List[Vehicle]
        self._assignment = None
        self._result_routes = None          # type: Optional[List[VehicleRoute]]

    def prepare_model(self, distance_mode: 'str' = 'real') -> None:
        """Query all entry in database to create a data model for CVRP."""
        self.__init__()
        # if self._initialized:
        #     current_app.logger.warn('Model already been initialized')
        #     return

        self._add_orders(Order.query.order_by(Order.id).all())
        self._add_vehicles(Vehicle.query.all())
        self._compute_distance_matrix(distance_mode)
        self._initialized = True

    def _add_orders(self, orders: List[Order]) -> None:
        self.order_list = orders
        for odr in orders:
            self.addresses.append(Coord(lat=odr.lat, lng=odr.lng))
            self.demands.append(int(odr.load))

        current_app.logger.info(f'Added {len(orders)} orders to data model.')

    def _add_vehicles(self, vehicles: List[Vehicle]) -> None:
        self.vehicle_list = vehicles
        for veh in vehicles:
            self.vehicle_capacities.append(int(veh.capacity))

        current_app.logger.info(f'Added {len(vehicles)} vehicles to data model.')

    def _compute_distance_matrix(self, mode: str) -> None:
        current_app.logger.debug('Building distance matrix')
        current_app.logger.debug(f'Addresses lng-lat: {self.addresses}')
        current_app.logger.debug(f'Demands: {self.demands}')
        current_app.logger.debug(f'Vehicle capacities: {self.vehicle_capacities}')

        N = len(self.addresses)

        if mode == 'utm':
            self.distance_matrix = np.zeros((N, N), np.int)
            for i in range(N):
                for j in range(i + 1, N):
                    self.distance_matrix[i][j] = self.distance_matrix[j][i] \
                        = self.addresses[i].utm_dist(self.addresses[j])
        elif mode == 'real':
            order_id_sequence = [order.id for order in self.order_list]
            if DistanceMatrix.isupdated():
                self.distance_matrix = DistanceMatrix.get_distance_matrix(order_id_sequence)
            else:
                with MatrixService() as service:
                    self.distance_matrix = np.array(service.request(self.addresses),
                                                    np.int)
                    DistanceMatrix.update_table(order_id_sequence, self.distance_matrix)
        else:
            raise ValueError(f'Invalid mode ({mode})')

    def solve(self):
        if not self._initialized:
            current_app.logger.error('Data model uninitialized when calling solve()')
            return None

        current_app.logger.info('Solving CVRP problem')
        manager = pywrapcp.RoutingIndexManager(self.distance_matrix.shape[0],
                                               self.vehicle_number,
                                               self.depot)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index: int, to_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self.distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        def demand_callback(from_index: int) -> int:
            from_node = manager.IndexToNode(from_index)
            return self.demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(demand_callback_index,
                                                0,
                                                self.vehicle_capacities,
                                                True,
                                                'Capacity')

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = \
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

        self._assignment = routing.SolveWithParameters(search_parameters)
        self._result_routes = VehicleRoute.from_cvrp_solution(self, manager, routing, self._assignment)
        current_app.logger.debug(f'Solution: {self._result_routes}')
        return self._result_routes

    @property
    def vehicle_number(self) -> int:
        return len(self.vehicle_capacities)

    @property
    def is_solved(self) -> bool:
        return self._assignment is not None

    @property
    def result_routes(self):
        if not self.is_solved:
            return None
        return self._result_routes


class VehicleRoute:
    def __init__(self, data_model: DataModel,
                 vehicle_id: int,
                 route_indices: List[int] = [],
                 route_distance: float = 0,
                 route_load: float = 0):
        # Index of the vehicle (0-indexing) in the CVRP problem
        # note that this is different from id in database
        self.vehicle_id = vehicle_id            # type: int

        # Order indices (0-indexing) for this vehicle in the CVRP problem.
        # The first and the last element in this list should be 0, indicating
        # the depot as the starting and final location
        self.route_indices = route_indices      # type: List[int]

        # Total distance in meters
        self.route_distance = route_distance    # type: float

        # Total load
        self.route_load = route_load            # type: float

        self._data_model = data_model           # type: DataModel
        self._path_str = ''                     # type: str
        self._path_data = []                    # type: List

    def __repr__(self):
        return str({
            attr: self.__getattribute__(attr) for attr in
            {'vehicle_id', 'route_indices', 'route_distance', 'route_load'}
        })

    @property
    def path(self):
        self._retrieve_directions()
        return self._path_str

    @property
    def path_data(self):
        self._retrieve_directions()
        return self._path_data

    def _retrieve_directions(self) -> None:
        if self._path_str or self._path_data:
            # Already retrieved
            return

        # In case this vehicle have no orders to work on.
        # Have not encountered yet.
        if type(self.route_indices) is not list or len(self.route_indices) < 3:
            self._path_str = 'No route required'
            self._path_data = []

        vehicle = self._data_model.vehicle_list[self.vehicle_id]

        # Again, note that index 0 is the depot, thus we have to
        # offset the idx here by -1 when retrieving from order database
        addresses = [self._data_model.order_list[idx-1].address for idx in self.route_indices[1:-1]]
        self._path_str = f"{vehicle.vehiclename}: {' > '.join(addresses)}" \
            f" | distance: {self.route_distance / 1000} km | load {self.route_load}"

        def query_googlemap_direction(orig_latlng: str, dest_latlng: str) -> List[List[float]]:
            current_app.logger.debug(f'Searching direction for {orig_latlng} and {dest_latlng}')
            gmap_direction = gmaps.directions(orig_latlng, dest_latlng,
                                              mode='driving')
            polyline_string = gmap_direction[0]['overview_polyline']['points']
            polyline = self._decode_polyline(polyline_string)
            return polyline

        current_app.logger.info(f'Retrieving direction for route indices {self.route_indices}')
        self._path_data += query_googlemap_direction(
            DEPOT_COORD.latlng,
            self._data_model.addresses[self.route_indices[1]].latlng)

        for idx in range(1, len(self.route_indices) - 2):
            self._path_data += query_googlemap_direction(
                self._data_model.addresses[self.route_indices[idx]].latlng,
                self._data_model.addresses[self.route_indices[idx+1]].latlng)

        self._path_data += query_googlemap_direction(
            self._data_model.addresses[self.route_indices[-2]].latlng,
            DEPOT_COORD.latlng)

    def _decode_polyline(self, polyline_string) -> List[List[float]]:
        index, lat, lng = 0, 0, 0
        coordinates = []
        changes = {'latitude': 0, 'longitude': 0}

        # Coordinates have variable length when encoded, so just keep
        # track of whether we've hit the end of the string. In each
        # while loop iteration, a single coordinate is decoded.
        while index < len(polyline_string):
            # Gather lat/lon changes, store them in a dictionary to apply them later
            for unit in ['latitude', 'longitude']:
                shift, result = 0, 0

                while True:
                    byte = ord(polyline_string[index]) - 63
                    index += 1
                    result |= (byte & 0x1f) << shift
                    shift += 5
                    if not byte >= 0x20:
                        break

                if (result & 1):
                    changes[unit] = ~(result >> 1)
                else:
                    changes[unit] = (result >> 1)

            lat += changes['latitude']
            lng += changes['longitude']

            coordinates.append([lat / 100000.0, lng / 100000.0])

        return coordinates

    @classmethod
    def from_cvrp_solution(cls, data_model: DataModel,
                           manager: pywrapcp.RoutingIndexManager,
                           routing: pywrapcp.RoutingModel,
                           assignment) -> 'Optional[List[VehicleRoute]]':
        if not assignment:
            return None

        res = []        # type: List[VehicleRoute]
        for vehicle_id in range(data_model.vehicle_number):
            index = routing.Start(vehicle_id)
            route_indices = []      # type: List[int]
            route_distance = 0      # float
            route_load = 0          # float

            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route_indices.append(node_index)
                route_load += data_model.demands[node_index]

                previous_index = index
                index = assignment.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id)

            route_indices.append(0)     # returns to depot
            res.append(cls(data_model, vehicle_id, route_indices, route_distance, route_load))

        current_app.logger.debug('CVRP Solution:\n{res}')
        return res
