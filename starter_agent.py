#Write the file to a .py script

from kaggle_environments.envs.halite.helpers import *
import random

#### ATTRIBUTES THAT YOUR AGENT WILL TRACK ####
turn = 0

#How much halite should a space have for a ship to harvest it?
target_halite = 120

#How much halite should a space have for a ship to stop harvesting?
min_halite = 100

#How much halite should the ship be able to collect before returning to base?
desired_cargo = 100

#What's the maximum number of ships we should have?
max_ships = 8

#What's the maximum number of shipyards we should have?
max_shipyards = 2

#What's the maximum amount of halite that a shipyard can be build on top of? This destroys the Halite underneath
acceptable_halite_for_shipyard = 0

#Directions a ship can move
directions = [ShipAction.NORTH, ShipAction.EAST, ShipAction.SOUTH, ShipAction.WEST]

# Keeps track of what each ship is currently doing
ship_states = {}

#Keeps track of the current path which the agent is on
current_path = {}

#Offset coordinates used for navigation
offsets = [[0, 1],[0, -1],[1, 0],[-1, 0]]

#The list of points representing the ships' navigation
next_points = []

#Other variables in the game
num_ships = 1
num_shipyards = 0

### FUNCTIONS USED BY YOUR AGENT ###

# Function to returns best direction to move from one position (fromPos) to another (toPos)
# Example: If I'm at pos 0 and want to get to pos 55, which direction should I choose?
def getDirTo(fromPos, toPos, size):
    fromX, fromY = divmod(fromPos[0], size), divmod(fromPos[1], size)
    toX, toY = divmod(toPos[0], size), divmod(toPos[1], size)
    if fromY < toY: return ShipAction.NORTH
    if fromY > toY: return ShipAction.SOUTH
    if fromX < toX: return ShipAction.EAST
    if fromX > toX: return ShipAction.WEST
    
#Data structure for defining the destinations that an agent must follow on its path
class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

#Define whether or not the "current" point is the space to which the ship wants to navigate

#If in COLLECT state, return whether it has collected enough halite
#If in DEPOSIT state, return whether it has reached a shipyard yet
#Note that "current" is a Node
def is_goal(current, board, ship):
    p = Point(current.x, current.y)
    
    #Test if the ship's state is currently being tracked
    if ship.id in ship_states:
        if ship_states[ship.id] == "COLLECT":
            return board.cells[p].halite >= target_halite
        if ship_states[ship.id] == "DEPOSIT":
            for shipyard in board.current_player.shipyards:
                return p == shipyard.position
        if ship_states[ship.id] == "CONSTRUCT":
            return board.cells[p].halite <= acceptable_halite_for_shipyard and p not in [shipyard.position for shipyard in board.current_player.shipyards]

#Return a list of nodes that neighbor the current node that are valid moves
def get_neighbors(node, board):
    neighbors = []
    for offset in offsets:
        x = node.x + offset[0]
        y = node.y + offset[1]
        p = Point(x, y)
        #Provided this point is actually on the board, and not occupied by another ship,
        # and another ship is not moving there next turn, add the point as a feasible neighbor
        if p in board.cells and not board.cells[p].ship_id and p not in next_points:
            neighbors.append(Node(x, y))
    return neighbors

#Take an end node of a path and generate a list of nodes that represent that path
def get_path(node, start):
    path = [node]
    while node.parent != start:
        path.append(node.parent)
        node = node.parent
    path.reverse()
    return path

# BREADTH-FIRST SEARCH #
#Searches for the "goal" point of the specified ship, starting from the "source" point
#The goal depends on the ship's state (ex. if in COLLECT, searches for a space with enough halite)
#Note that source is a "Node" object
def locate_goal(source, board, ship):
    queue = set()
    visited = set()
    queue.add(source)
    while queue:
        #Check the next node as the "current"
        current = queue.pop()
        
        #If the "current" space is the space that the ship is looking for, generate and return a path to that goal
        if is_goal(current, board, ship):
            return get_path(current, source)
        
        #Otherwise, if goal not yet found, add neighboring spaces to queue to be tested
        for neighbor in get_neighbors(current, board):
            if neighbor not in visited:
                visited.add(neighbor)
                neighbor.parent = current
                queue.add(neighbor)
                
#This method is used to determine what goal a ship should pursue
def determine_state(ship, me):
    if (num_shipyards < max_shipyards and num_ships > 1 and me.halite >= 500) or (num_shipyards == 0 and me.halite + ship.halite >= 1000):
        ship_states[ship.id] = "CONSTRUCT"
    elif ship.halite >= desired_cargo:  # If cargo is too low, collect halite
        ship_states[ship.id] = "DEPOSIT"
    else: #Otherwise, collect halite
        ship_states[ship.id] = "COLLECT"
        
    
#Only stay still if ship is on a valid space to collect Halite
def determine_if_moving(ship, board):
    if ship_states[ship.id] == "COLLECT" or ship_states[ship.id] == "CONSTRUCT":
        return not is_goal(Node(ship.position.x, ship.position.y), board, ship)
    else:
        return True
        
def get_next_move(ship, board, size):
    #Calculate path to ship's goal, based on their current state
    current_path[ship.id] = locate_goal(Node(ship.position.x, ship.position.y), board, ship)
    
    #If the ship hasn't reached the end of its path yet, calculate the direction to the next node in the path
    # and travel in that direction
    if ship.id in current_path and not ship.next_action:
        ship_path = current_path[ship.id]
                
        #If the current path has not yet been traveled by the ship, move to the node in the path
        if ship_path:
            next_node = ship_path[0]
            p = Point(next_node.x, next_node.y)
                    
            #If the next id is not a ship and not a position that another ship is going to, move to that space
            if not board.cells[p].ship_id and p not in next_points:
                direction = getDirTo(ship.position, p, size)
                if direction:
                    ship.next_action = direction
                    ship_path.remove(p)
                    next_points.append(p)
            #If the ship cannot move to the space it wants to, move it to a random valid space
            else:
                random_points = get_neighbors(ship.position, board)
                if random_points:
                    next_node = random.choice(random_points)
                    p = Point(next_node.x, next_node.y)
                    direction = getDirTo(ship.position, p, size)
                    if direction:
                        ship.next_action = direction 
                        next_points.append(p)

def spawn_ship(me):
    #Only shipyards not currently occupied are valid for conversion
    valid_shipyards = [shipyard for shipyard in me.shipyards if shipyard.position not in [ship.position for ship in me.ships]]
    if len(valid_shipyards) > 0:
        constructing_shipyard = random.choice(valid_shipyards)
        constructing_shipyard.next_action = ShipyardAction.SPAWN
        next_points.append(constructing_shipyard.position)
        
### API CALL - USED BY SIMULATOR ###
# Returns the commands we send to our ships and shipyards
#This controls what the agent actually does each turn
def agent(obs, config):
    global turn
    global next_points
    global num_ships
    global num_shipyards
    turn += 1
    size = config.size
    board = Board(obs, config)
    me = board.current_player
    
    num_ships = len(me.ships)
    num_shipyards = len(me.shipyards)
    
    #Create a list of ships
    ships_list = me.ships

    # If there are not enough ships, spawn a ship at a random shipyard
    if num_ships < max_ships and num_shipyards > 0 and me.halite > 500:
        spawn_ship(me)          

    #Set the next action of each ship
    for ship in ships_list:
        
        #If ship doesn't have a current state, give it a state (aka a goal to pursue)
        if ship.next_action is None:
            determine_state(ship, me)
        
        #Decide which action to take next
        if ship.id in ship_states and determine_if_moving(ship, board):
            get_next_move(ship, board, size)
        #If the ship has reached valid area for shipyard, convert to shipyard
        elif ship_states[ship.id] == "CONSTRUCT":
            ship.next_action = ShipAction.CONVERT
            num_shipyards += 1
        #Otherwise, let other ships know that this ship is remaining stationary
        else:
            next_points.append(ship.position)

    #Now that all the ships have been calculated, clear the next_points to prepare for the next round (otherwise ships will freeze)
    next_points.clear()
    return me.next_actions
