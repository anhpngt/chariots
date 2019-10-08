from typing import List
from typing import Optional

import numpy as np
from flask import current_app
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2

from app.constants import DEPOT_COORD
from app.database.models import Order
from app.database.models import Vehicle
from app.mapbox import MatrixService
from app.types import Coord


class DataModel:
    def __init__(self):
        self.addresses = [DEPOT_COORD]      # type: List[Coord]
        self.demands = [0]                  # type: List[int]
        self.depot = 0                      # type: int
        self.vehicle_capacities = []        # type: List[int]
        self.distance_matrix = []           # type: List

    def prepare_model(self,
                      orders: 'Optional[List[Order]]' = None,
                      vehicles: 'Optional[List[Vehicle]]' = None,
                      distance_mode: 'str' = 'real') -> None:
        self.add_orders(orders or Order.query.all())
        self.add_vehicles(vehicles or Vehicle.query.all())
        self.compute_distance_matrix(distance_mode)

    def add_orders(self, orders: List[Order]) -> None:
        for odr in orders:
            self.addresses.append(Coord(lat=odr.lat, lng=odr.lng))
            self.demands.append(int(odr.load))

    def add_vehicles(self, vehicles: List[Vehicle]) -> None:
        for veh in vehicles:
            self.vehicle_capacities.append(int(veh.capacity))

    def compute_distance_matrix(self, mode: str) -> None:
        N = len(self.addresses)

        if mode == 'utm':
            self.distance_matrix = np.zeros((N, N), np.int)
            for i in range(N):
                for j in range(i + 1, N):
                    self.distance_matrix[i][j] = self.distance_matrix[j][i] \
                        = self.addresses[i].utm_dist(self.addresses[j])
        elif mode == 'real':
            with MatrixService() as service:
                self.distance_matrix = np.array(service.request(self.addresses),
                                                np.int)
        else:
            raise ValueError(f'Invalid mode ({mode})')

    @property
    def vehicle_number(self) -> int:
        return len(self.vehicle_capacities)


def print_cvrp_solution(data: DataModel,
                        manager: pywrapcp.RoutingIndexManager,
                        routing: pywrapcp.RoutingModel,
                        assignment) -> List:
    # html_name = './app/templates/res.html'
    # depot_latlon = str2ll(depot)
    # gmap = gmplot.GoogleMapPlotter(depot_latlon[0], depot_latlon[1], 15, api)

    total_distance = 0
    total_load = 0

    routes = []
    for vehicle_id in range(data.vehicle_number):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0

        route = []
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data.demands[node_index]
            plan_output += f' {node_index} Load({route_load}) -> '

            route.append(node_index)
            previous_index = index
            index = assignment.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        route.append(0)

        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)

        total_distance += route_distance
        total_load += route_load
        routes.append([route, route_distance, route_load])

    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {}'.format(total_load))

    return routes


def solve_cvrp(data_model: DataModel):
    manager = pywrapcp.RoutingIndexManager(len(data_model.distance_matrix),
                                           data_model.vehicle_number,
                                           data_model.depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data_model.distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        return data_model.demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(demand_callback_index,
                                            0,
                                            data_model.vehicle_capacities,
                                            True,
                                            'Capacity')

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = \
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    assignment = routing.SolveWithParameters(search_parameters)
    if assignment:
        routes = print_cvrp_solution(data_model, manager, routing, assignment)
        return routes
    else:
        return None
