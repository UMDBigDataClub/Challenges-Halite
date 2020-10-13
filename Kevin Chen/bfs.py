offsets = [
    [0, 1],
    [0, -1],
    [1, 0],
    [-1, 0]
]


def get_neighbors(node):
    neighbors = set()
    for offset in offsets:
        x = node.x + offset[0]
        y = node.y + offset[1]
        # TODO: check if square has friendly ship or if current ship is carrying cargo to avoid collisions
        neighbors.add(Node(x, y))
    return neighbors


def get_path(node):
    path = [node]
    while node.parent is not None:
        path.append(node.parent)
        node = node.parent
    path.reverse()
    return path


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


def bfs(source, destination):
    queue = [source]
    visited = set()
    while queue:
        current = queue.pop(0)
        if current == destination:
            return get_path(current)
        for neighbor in get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                neighbor.parent = current
                queue.append(neighbor)


path = bfs(Node(0, 0), Node(10, 10))
for node in path:
    print(node.x, node.y)
