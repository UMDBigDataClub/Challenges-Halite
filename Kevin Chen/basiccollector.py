from kaggle_environments.envs.halite.helpers import *


# Returns best direction to move from one position (fromPos) to another (toPos)
# Example: If I'm at pos 0 and want to get to pos 55, which direction should I choose?
def getDirTo(fromPos, toPos, size):
    fromX, fromY = divmod(fromPos[0], size), divmod(fromPos[1], size)
    toX, toY = divmod(toPos[0], size), divmod(toPos[1], size)
    if fromY < toY: return ShipAction.NORTH
    if fromY > toY: return ShipAction.SOUTH
    if fromX < toX: return ShipAction.EAST
    if fromX > toX: return ShipAction.WEST


# Directions a ship can move
directions = [ShipAction.NORTH, ShipAction.EAST, ShipAction.SOUTH, ShipAction.WEST]

# Will keep track of whether a ship is collecting halite or carrying cargo to a shipyard
ship_states = {}

current_path = {}

offsets = [
    [0, 1],
    [0, -1],
    [1, 0],
    [-1, 0]
]


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


def get_path(node, start):
    path = [node]
    while node.parent != start:
        path.append(node.parent)
        node = node.parent
    path.reverse()
    return path


def is_goal(current, board, ship):
    p = Point(current.x, current.y)
    if ship.id in ship_states:
        if ship_states[ship.id] == "COLLECT":
            return board.cells[p].halite >= 250
        if ship_states[ship.id] == "DEPOSIT":
            for shipyard in board.current_player.shipyards:
                return p == shipyard.position


def get_neighbors(node, board):
    neighbors = set()
    for offset in offsets:
        x = node.x + offset[0]
        y = node.y + offset[1]
        p = Point(x, y)
        if p in board.cells and not board.cells[p].ship_id:
            neighbors.add(Node(x, y))
    return neighbors


def bfs(source, board, ship):
    queue = set()
    visited = set()
    queue.add(source)
    while queue:
        current = queue.pop()
        if is_goal(current, board, ship):
            return get_path(current, source)
        for neighbor in get_neighbors(current, board):
            if neighbor not in visited:
                visited.add(neighbor)
                neighbor.parent = current
                queue.add(neighbor)


# Returns the commands we send to our ships and shipyards
def agent(obs, config):
    size = config.size
    board = Board(obs, config)
    me = board.current_player

    # If there are no ships, use first shipyard to spawn a ship.
    if len(me.ships) == 0 and len(me.shipyards) > 0:
        me.shipyards[0].next_action = ShipyardAction.SPAWN

    # If there are no shipyards, convert first ship into shipyard.
    if len(me.shipyards) == 0 and len(me.ships) > 0:
        me.ships[0].next_action = ShipAction.CONVERT

    for ship in me.ships:
        if ship.next_action is None:

            ### Part 1: Set the ship's state
            if ship.halite < 200:  # If cargo is too low, collect halite
                ship_states[ship.id] = "COLLECT"
            if ship.halite > 500:  # If cargo gets very big, deposit halite
                ship_states[ship.id] = "DEPOSIT"

        if ship.id in ship_states and not (ship_states[ship.id] == "COLLECT" and board.cells[ship.position].halite >= 250):
            if ship.id not in current_path or not current_path[ship.id]:
                current_path[ship.id] = bfs(Node(ship.position.x, ship.position.y), board, ship)
            if ship.id in current_path and not ship.next_action:
                ship_path = current_path[ship.id]
                if ship_path:
                    next_node = ship_path.pop(0)
                    direction = getDirTo(ship.position, Point(next_node.x, next_node.y), size)
                    if direction:
                        ship.next_action = direction

    return me.next_actions
