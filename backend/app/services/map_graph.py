import heapq
from typing import Dict, List, Tuple


MAP_GRAPH: Dict[str, Dict[str, float]] = {
    "entrance": {"main_hall": 2, "gym": 5},
    "main_hall": {"entrance": 2, "multipurpose_room": 3, "stairs": 2},
    "multipurpose_room": {"main_hall": 3, "gym": 4},
    "gym": {"entrance": 5, "multipurpose_room": 4},
    "stairs": {"main_hall": 2, "second_floor": 3},
    "second_floor": {"stairs": 3},
}


def nearest_node(location_x: float | None, location_y: float | None) -> str:
    if location_x is None or location_y is None:
        return "main_hall"
    if location_x < 20 and location_y < 20:
        return "entrance"
    if location_x >= 20 and location_y < 20:
        return "multipurpose_room"
    if location_y >= 20:
        return "gym"
    return "main_hall"


def shortest_path(start: str, goal: str) -> Tuple[float, List[str]]:
    queue = [(0.0, start, [start])]
    visited = set()

    while queue:
        distance, node, path = heapq.heappop(queue)
        if node == goal:
            return distance, path
        if node in visited:
            continue
        visited.add(node)

        for next_node, weight in MAP_GRAPH.get(node, {}).items():
            if next_node not in visited:
                heapq.heappush(queue, (distance + weight, next_node, path + [next_node]))

    raise ValueError(f"No route from {start} to {goal}")
