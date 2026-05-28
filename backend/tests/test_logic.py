from app.services.map_graph import nearest_node, shortest_path


def test_nearest_node():
    assert nearest_node(5, 5) == "entrance"
    assert nearest_node(25, 10) == "multipurpose_room"
    assert nearest_node(30, 30) == "gym"
    assert nearest_node(None, None) == "main_hall"


def test_shortest_path():
    distance, path = shortest_path("entrance", "second_floor")

    assert distance > 0
    assert path[0] == "entrance"
    assert path[-1] == "second_floor"
