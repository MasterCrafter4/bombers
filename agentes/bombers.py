from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid  
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Contenido del escenario (formato completo)
scenario_content = """1001 1000 1000 1000 1100 0001 1000 1100
0001 0000 0110 0011 0010 0010 0010 0100
0000 0000 1000 1000 1000 1100 1001 0100
0011 0110 0011 0000 0010 0010 0010 0010
1001 1000 1000 0000 1100 1001 1100 1101
0011 0010 0000 0010 0010 0010 0010 0110
2 4 v
5 1 f
5 8 v
2 2
2 3
3 2
3 3 
3 4
3 5
4 4
5 6
5 7
6 6
1 3 1 4
2 5 2 6
2 8 3 8
3 2 3 3
4 4 5 4
4 6 4 7
6 5 6 6
6 7 6 8
1 6
3 1
4 8
6 3"""

class ScenarioParser:
    @staticmethod
    def _parse_grid_walls(lines):
        """Parses the first 6 lines of the scenario to get the walls"""
        original_grid = np.zeros((6, 8, 4), dtype=int)
        for i, line in enumerate(lines[:6]):
            for j, cell in enumerate(line.strip().split()):
                original_grid[i, j] = [int(d) for d in cell]
        
        # Create extended grid with perimeter (8, 10, 4)
        grid = np.zeros((8, 10, 4), dtype=int)

        # Copy original scenario into center (1:7, 1:9)
        grid[1:7, 1:9] = original_grid

        # Add walls in outer perimeter
        grid[0, 1:9, 0] = 1  # North
        grid[7, 1:9, 2] = 1  # South
        grid[1:7, 0, 3] = 1  # West
        grid[1:7, 9, 1] = 1  # East
        
        print("Walls parsed correctly.")
        return grid

    @staticmethod
    def _parse_pois(lines):
        """Parses the Points of Interest (POI) lines"""
        pois = []
        poi_lines = lines[6:9]  # 3 lines after the walls
        
        for line in poi_lines:
            parts = line.strip().split()
            if len(parts) == 3:
                row, col, poi_type = parts
                # Convert to 0-based coordinates and consider perimeter (+1)
                row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
                pois.append((row_idx, col_idx, poi_type))
        
        print(f"POIs parsed: {pois}")
        return pois

    @staticmethod
    def _parse_fires(lines):
        """Parses the initial fire lines"""
        fires = []
        fire_lines = lines[9:19]  # 10 lines after POIs
        
        for line in fire_lines:
            parts = line.strip().split()
            if len(parts) == 2:
                row, col = parts
                # Convert to 0-based coordinates and consider perimeter (+1)
                row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
                fires.append((row_idx, col_idx))
        
        print(f"Initial fires parsed: {fires}")
        return fires

    @staticmethod
    def _parse_doors(lines):
        """Parses the door lines"""
        doors = []
        door_lines = lines[19:27]  # 8 lines after fires
        
        for line in door_lines:
            parts = line.strip().split()
            if len(parts) == 4:
                r1, c1, r2, c2 = parts
                # Convert to 0-based coordinates and consider perimeter (+1)
                r1_idx, c1_idx = int(r1) - 1 + 1, int(c1) - 1 + 1
                r2_idx, c2_idx = int(r2) - 1 + 1, int(c2) - 1 + 1
                doors.append(((r1_idx, c1_idx), (r2_idx, c2_idx)))
        
        print(f"Doors parsed: {doors}")
        return doors

    @staticmethod
    def _parse_entries(lines):
        """Parses the firefighter entry lines"""
        entries = []
        entry_lines = lines[27:31]  # 4 lines after doors
        
        for line in entry_lines:
            parts = line.strip().split()
            if len(parts) == 2:
                row, col = parts
                # Convert to 0-based coordinates and consider perimeter (+1)
                row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
                entries.append((row_idx, col_idx))
        
        print(f"Entries parsed: {entries}")
        return entries

    @staticmethod
    def parse_scenario(scenario_text):
        """Main function that parses the entire scenario content"""
        lines = scenario_text.strip().split('\n')
        
        # Validate that there are enough lines
        if len(lines) < 31:
            print(f"Error: The scenario must have at least 31 lines, it has {len(lines)}")
            return None
        
        # Parse each component
        grid = ScenarioParser._parse_grid_walls(lines)
        pois = ScenarioParser._parse_pois(lines)
        fires = ScenarioParser._parse_fires(lines)
        doors = ScenarioParser._parse_doors(lines)
        entries = ScenarioParser._parse_entries(lines)
        
        # Create scenario dictionary
        scenario = {
            "grid_walls": grid,
            "pois": pois,
            "fires": fires,
            "doors": doors,
            "entries": entries
        }
        
        print("Scenario completely parsed.")
        return scenario
    
    @staticmethod
    def compute_door_positions(doors):
        """Calculates door positions for visualization"""
        door_positions = []
        for (r1, c1), (r2, c2) in doors:
            # Determine in which direction the door is
            if r1 == r2:  # Horizontal door (east-west)
                if c1 < c2:  # c1 is to the left of c2
                    door_positions.append((r1, c1, 1))  # Door on the east of cell 1
                else:
                    door_positions.append((r1, c2, 1))  # Door on the east of cell 2
            else:  # Vertical door (north-south)
                if r1 < r2:  # r1 is above r2
                    door_positions.append((r1, c1, 2))  # Door on the south of cell 1
                else:
                    door_positions.append((r2, c2, 2))  # Door on the south of cell 2
        
        return door_positions

    @staticmethod
    def build_grid_state(scenario):
        """Builds a grid where each cell is a dictionary with complete state"""
        rows, columns = scenario["grid_walls"].shape[:2]
        
        # Create empty grid
        grid_state = np.empty((rows, columns), dtype=object)
        
        # Calculate door positions to identify cells with doors
        door_positions = ScenarioParser.compute_door_positions(scenario["doors"])
        
        # Initialize each cell
        for y in range(rows):
            for x in range(columns):
                # Get wall information
                walls = scenario["grid_walls"][y, x].tolist()
                
                # Check if there's fire
                fire = (y, x) in scenario["fires"]
                
                # Check if there's a door in any direction
                door = any((y, x, d) in door_positions for d in range(4))
                
                # Check if there's a POI and what type
                poi = None
                for p_y, p_x, p_type in scenario["pois"]:
                    if p_y == y and p_x == x:
                        poi = p_type
                        break
                
                # Create cell dictionary
                cell = {
                    "walls": walls,
                    "fire": fire,
                    "smoke": False,
                    "damage": 0,
                    "door": door,
                    "poi": poi
                }
                
                # Assign to grid
                grid_state[y, x] = cell
        
        return grid_state

class DirectionHelper:
    # Constants for directions
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    
    # Displacement vectors for each direction (dx, dy)
    DIRECTIONS = [
        (0, -1),  # North: no change in x, -1 in y
        (1, 0),   # East: +1 in x, no change in y
        (0, 1),   # South: no change in x, +1 in y
        (-1, 0)   # West: -1 in x, no change in y
    ]
    
    # Direction names for messages
    DIRECTION_NAMES = ["north", "east", "south", "west"]
    
    @staticmethod
    def get_adjacent_position(x, y, direction):
        """Gets the adjacent position in the specified direction"""
        dx, dy = DirectionHelper.DIRECTIONS[direction]
        return x + dx, y + dy
    
    @staticmethod
    def get_opposite_direction(direction):
        """Gets the opposite direction (0↔2, 1↔3)"""
        return (direction + 2) % 4
    
    @staticmethod
    def is_perimeter(model, x, y):
        """Checks if a position is on the perimeter"""
        return (x == 0 or x == model.grid.width - 1 or y == 0 or y == model.grid.height - 1)
    
    @staticmethod
    def get_wall_key(y, x, direction):
        """Gets the key for a wall in the specified direction"""
        return (y, x, direction)
    
    @staticmethod
    def has_wall(model, y, x, direction):
        """Checks if there's a wall in the specified direction"""
        # Check if there's a wall in the current cell
        return model.grid_state[y, x]["walls"][direction] == 1
    
    @staticmethod
    def is_wall_destroyed(model, y, x, direction):
        """Checks if a wall is destroyed (has 2 or more damage points)"""
        wall_key = DirectionHelper.get_wall_key(y, x, direction)
        return wall_key in model.wall_damage and model.wall_damage[wall_key] >= 2
    
    @staticmethod
    def can_pass_wall(model, y, x, direction):
        """Checks if you can pass through a wall (no wall or it's destroyed)"""
        return not DirectionHelper.has_wall(model, y, x, direction) or DirectionHelper.is_wall_destroyed(model, y, x, direction)
    
    @staticmethod
    def is_door(model, y, x, direction):
        """Checks if there's a door in the specified direction"""
        door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
        door_key = (y, x, direction)
        return door_key in door_positions
    
    @staticmethod
    def get_door_state(model, y, x, direction):
        """Gets the state of a door (open/closed/destroyed)"""
        door_key = (y, x, direction)
        
        if door_key not in ScenarioParser.compute_door_positions(model.scenario["doors"]):
            return None  # Not a door
        
        if door_key in model.door_states:
            return model.door_states[door_key]  # "open" or "closed"
        else:
            return "destroyed"  # If not in door_states but is a door, it's destroyed
    
    @staticmethod
    def is_entry(model, x, y):
        """Checks if a position is an entry point"""
        return (x, y) in [(e[1], e[0]) for e in model.scenario["entries"]]
    
    @staticmethod
    def damage_wall(model, y, x, direction):
        """Adds a damage point to a wall and checks if it gets destroyed"""
        wall_key = DirectionHelper.get_wall_key(y, x, direction)
        
        # Add damage
        if wall_key not in model.wall_damage:
            model.wall_damage[wall_key] = 1
        else:
            model.wall_damage[wall_key] += 1
        
        model.damage_counters += 1
        
        # If the wall has 2 damage points, it's destroyed
        if model.wall_damage[wall_key] >= 2:
            # Destroy the wall in the current cell
            model.grid_state[y, x]["walls"][direction] = 0
            
            # Also destroy the corresponding wall in the adjacent cell
            new_x, new_y = DirectionHelper.get_adjacent_position(x, y, direction)
            opposite_direction = DirectionHelper.get_opposite_direction(direction)
            
            # Verify that the adjacent cell is within limits
            if 0 <= new_y < model.grid.height and 0 <= new_x < model.grid.width:
                model.grid_state[new_y, new_x]["walls"][opposite_direction] = 0
                
            return True  # Wall destroyed
        
        return False  # Wall damaged but not destroyed

class GameMechanics:
    @staticmethod
    def advance_fire(model):
        """Propagates fire through the scenario according to Flash Point: Fire Rescue rules"""
        rows, cols = model.grid_state.shape
        
        # Initialize counters if they don't exist
        if not hasattr(model, 'victims_lost'):
            model.victims_lost = 0
        if not hasattr(model, 'damage_counters'):
            model.damage_counters = 0
        
        # 1. SIMULATE DICE ROLL TO ADD RANDOM FIRE
        # Generate valid random coordinates (not in perimeter)
        random_row = model.random.randint(1, rows-2)
        random_col = model.random.randint(1, cols-2)
        
        # Check cell state
        cell = model.grid_state[random_row, random_col]
        
        print(f"🎲 Dice roll: Ignition point at ({random_col},{random_row})")
        
        # Case 1: Cell with no fire or smoke -> Add SMOKE (not fire)
        if not cell["fire"] and not cell["smoke"]:
            cell["smoke"] = True  # Place smoke instead of fire
            print(f"💨 Smoke added at ({random_col},{random_row})")
        
        # Case 2: Cell with smoke -> Convert to fire
        elif not cell["fire"] and cell["smoke"]:
            cell["fire"] = True
            cell["smoke"] = False
            if (random_row, random_col) not in model.scenario["fires"]:
                model.scenario["fires"].append((random_row, random_col))
            print(f"🔥 Fire spreads to ({random_col},{random_row}): had smoke → now is fire.")
            
            # Check if there's a victim in the cell
            if cell["poi"] == "v":
                cell["poi"] = None
                model.victims_lost += 1
                print(f"💀 Victim at ({random_col},{random_row}) died in the fire")
                
                # Update POIs in the scenario
                for i, poi in enumerate(model.scenario["pois"]):
                    if poi[0] == random_row and poi[1] == random_col:
                        model.scenario["pois"].pop(i)
                        break
        
        # Case 3: Cell with fire -> EXPLOSION
        elif cell["fire"]:
            print(f"💥 EXPLOSION! Fire hit a cell that already had fire: ({random_col},{random_row})")
            
            # Generate explosion in 4 directions: North, East, South, West
            for direction in range(4):
                GameMechanics.propagate_explosion(model, random_row, random_col, direction)
        
        # 2. SMOKE TO FIRE PROPAGATION (second phase)
        new_fires = []  # List of (y, x) where there will be new fire
        new_smokes = []  # List of (y, x) where there will be new smoke
        
        # Detect fire propagation
        for y in range(rows):
            for x in range(cols):
                # If the cell has fire, spread to adjacent cells
                if model.grid_state[y, x]["fire"]:
                    # Check propagation in all 4 directions
                    for direction in range(4):
                        # If there's no wall in this direction or wall is destroyed
                        if DirectionHelper.can_pass_wall(model, y, x, direction):
                            # Get adjacent cell coordinates
                            nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
                            
                            # Check if it's within limits
                            if 0 <= ny < rows and 0 <= nx < cols:
                                # Check if it's not in the perimeter
                                if not DirectionHelper.is_perimeter(model, nx, ny):
                                    # Check if adjacent cell doesn't have fire
                                    if not model.grid_state[ny, nx]["fire"]:
                                        if model.grid_state[ny, nx]["smoke"]:
                                            # If there's smoke, convert to fire
                                            new_fires.append((ny, nx))
                                        else:
                                            # If no smoke, add smoke
                                            new_smokes.append((ny, nx))
        
        # Apply the detected changes
        # First apply the new fires
        for y, x in new_fires:
            model.grid_state[y, x]["fire"] = True
            model.grid_state[y, x]["smoke"] = False  # Smoke becomes fire
            # Add to the fire list in the scenario
            fire_pos = (y, x)
            if fire_pos not in model.scenario["fires"]:
                model.scenario["fires"].append(fire_pos)
            # Print informative message
            print(f"🔥 Fire spreads to ({x},{y}): had smoke → now is fire.")
            
            # Check if there's a victim in the cell
            if model.grid_state[y, x]["poi"] == "v":
                model.grid_state[y, x]["poi"] = None
                model.victims_lost += 1
                print(f"💀 Victim at ({x},{y}) died in the fire")
                
                # Update POIs in the scenario
                for i, poi in enumerate(model.scenario["pois"]):
                    if poi[0] == y and poi[1] == x:
                        model.scenario["pois"].pop(i)
                        break
        
        # Then apply the new smokes (avoiding duplicates with new fires)
        for y, x in new_smokes:
            if (y, x) not in new_fires:  # Avoid duplicates
                model.grid_state[y, x]["smoke"] = True
                # Print informative message
                print(f"💨 Fire generates smoke at ({x},{y}).")

    @staticmethod
    def propagate_explosion(model, row, col, direction):
        """Propagates an explosion in the specified direction until finding an obstacle"""
        rows, cols = model.grid_state.shape
        
        # Determine the displacement direction
        dx, dy = DirectionHelper.DIRECTIONS[direction]
        dir_name = DirectionHelper.DIRECTION_NAMES[direction]
        
        print(f"💥 Explosion! Fire spreads to the {dir_name} from ({col},{row})")
        
        # Remove all doors adjacent to the original explosion target space
        if direction == DirectionHelper.NORTH:  # Only in the first direction to avoid duplicates
            # Find doors in the four cardinal directions
            door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
            
            # Check north
            north_door = (row, col, DirectionHelper.NORTH)
            if north_door in door_positions:
                if north_door in model.door_states:
                    del model.door_states[north_door]
                print(f"🚪 The explosion destroyed a door north of ({col},{row})")
            
            # Check east
            east_door = (row, col, DirectionHelper.EAST)
            if east_door in door_positions:
                if east_door in model.door_states:
                    del model.door_states[east_door]
                print(f"🚪 The explosion destroyed a door east of ({col},{row})")
            
            # Check south
            south_door = (row, col, DirectionHelper.SOUTH)
            if south_door in door_positions:
                if south_door in model.door_states:
                    del model.door_states[south_door]
                print(f"🚪 The explosion destroyed a door south of ({col},{row})")
            
            # Check west
            west_door = (row, col, DirectionHelper.WEST)
            if west_door in door_positions:
                if west_door in model.door_states:
                    del model.door_states[west_door]
                print(f"🚪 The explosion destroyed a door west of ({col},{row})")
        
        # Start propagation
        x, y = col, row
        wall_found = False
        
        while not wall_found:
            # Calculate new position
            new_x, new_y = x + dx, y + dy
            
            # Check if we're within limits
            if new_y < 0 or new_y >= rows or new_x < 0 or new_x >= cols:
                print(f"💥 Explosion stopped: reached the board edge at ({x},{y})")
                break
                
            # Check if we're in the perimeter (where it should not propagate)
            if DirectionHelper.is_perimeter(model, new_x, new_y):
                print(f"💥 Explosion stopped: reached the perimeter at ({new_x},{new_y})")
                break
            
            # NEW: First check if there's a door in the explosion's direction
            door_in_path = None
            door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
            
            door_in_path = (y, x, direction)
                
            if door_in_path in door_positions:
                # There's a door in the path, we remove it (regardless of open/closed state)
                if door_in_path in model.door_states:
                    del model.door_states[door_in_path]
                print(f"🚪 The explosion destroyed a door between ({x},{y}) and ({new_x},{new_y})")
                # Explosion continues after destroying the door
                y = new_y
                x = new_x
                continue
            
            # Check if there's a wall in the path (if no door)
            has_wall = DirectionHelper.has_wall(model, y, x, direction)
            wall_key = DirectionHelper.get_wall_key(y, x, direction)
            
            # Check if wall already has 2 damages (destroyed)
            wall_destroyed = DirectionHelper.is_wall_destroyed(model, y, x, direction)
                
            if has_wall and not wall_destroyed:
                # Add damage to the wall
                wall_destroyed = DirectionHelper.damage_wall(model, y, x, direction)
                
                print(f"🧱 Wall damaged between ({x},{y}) and ({new_x},{new_y}), total damage: {model.wall_damage[wall_key]}")
                
                if wall_destroyed:
                    print(f"🧱 Wall between ({x},{y}) and ({new_x},{new_y}) was destroyed")
                    # Explosion continues
                else:
                    # If the wall is not destroyed, the explosion stops
                    wall_found = True
                    break
            
            # If the wall was destroyed or there was no wall, explosion continues
            if not has_wall or wall_destroyed:
                # Advance to the new position
                x, y = new_x, new_y
                cell = model.grid_state[y, x]
                
                # If there's a victim in the cell, the victim dies
                if cell["poi"] == "v":
                    cell["poi"] = None
                    model.victims_lost += 1
                    print(f"💀 Victim at ({x},{y}) died in the explosion")
                    
                    # Update POIs in the scenario
                    for i, poi in enumerate(model.scenario["pois"]):
                        if poi[0] == y and poi[1] == x:
                            model.scenario["pois"].pop(i)
                            break
                
                # If there's smoke, it converts to fire
                if cell["smoke"]:
                    cell["smoke"] = False
                    cell["fire"] = True
                    if (y, x) not in model.scenario["fires"]:
                        model.scenario["fires"].append((y, x))
                    print(f"🔥 Explosion converts smoke to fire at ({x},{y})")
                
                # If no fire or smoke, add fire
                elif not cell["fire"]:
                    cell["fire"] = True
                    if (y, x) not in model.scenario["fires"]:
                        model.scenario["fires"].append((y, x))
                    print(f"🔥 Explosion spreads fire to ({x},{y})")
                
                # NEW: If there's already fire, generate a shockwave
                else:
                    print(f"🔥 Explosion hit a cell with fire at ({x},{y})")
                    print(f"⚡ A SHOCKWAVE is generated in the {dir_name} direction!")
                    # Start shockwave from this cell
                    GameMechanics.shockwave(model, y, x, direction)
                    # Explosion stops here because a shockwave was generated
                    break

    @staticmethod
    def shockwave(model, row, col, direction):
        """
        Propagates a shockwave in the specified direction
        when an explosion reaches a cell that already has fire
        """
        rows, cols = model.grid_state.shape
        
        # Determine the displacement direction
        dx, dy = DirectionHelper.DIRECTIONS[direction]
        dir_name = DirectionHelper.DIRECTION_NAMES[direction]
        
        print(f"⚡ SHOCKWAVE! Shockwave initiated to the {dir_name} from ({col},{row})")
        
        # Start shockwave propagation
        x, y = col, row
        stopped = False
        
        while not stopped:
            # Calculate new position
            new_x, new_y = x + dx, y + dy
            x, y = new_x, new_y  # Update current position
            
            # Check if we're within limits
            if y < 0 or y >= rows or x < 0 or x >= cols:
                print(f"⚡ Shockwave reached board edge at ({x-dx},{y-dy})")
                break
            
            # Check if there's a door in the advance direction from the previous position
            door_key = (y-dy, x-dx, direction)
            door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
            
            if door_key in door_positions:
                # Check if door is closed or open
                if door_key in model.door_states:
                    door_state = model.door_states[door_key]
                    if door_state == "cerrada":  # "closed"
                        # If closed, remove it and continue
                        del model.door_states[door_key]
                        print(f"⚡ Shockwave destroyed a closed door between ({x-dx},{y-dy}) and ({x},{y})")
                        # Continue propagation (don't stop)
                    else:
                        # If open, pass through it
                        print(f"⚡ Shockwave passed through an open door between ({x-dx},{y-dy}) and ({x},{y})")
                        # Continue propagation (don't stop)
                else:
                    # If door is not in door_states, it was already destroyed
                    print(f"⚡ Shockwave passed through a destroyed door between ({x-dx},{y-dy}) and ({x},{y})")
                    # Continue propagation (don't stop)
            else:
                # Check if there's a wall in the advance direction from the previous position
                has_wall = DirectionHelper.has_wall(model, y-dy, x-dx, direction)
                
                if has_wall:
                    # Check if wall already has 2 damages (destroyed)
                    wall_destroyed = DirectionHelper.is_wall_destroyed(model, y-dy, x-dx, direction)
                    
                    if wall_destroyed:
                        # If wall is destroyed, pass through it
                        print(f"⚡ Shockwave passed through a destroyed wall between ({x-dx},{y-dy}) and ({x},{y})")
                        # Continue propagation (don't stop)
                    else:
                        # If wall is not destroyed, damage it
                        wall_key = DirectionHelper.get_wall_key(y-dy, x-dx, direction)
                        DirectionHelper.damage_wall(model, y-dy, x-dx, direction)
                        
                        if wall_key in model.wall_damage:
                            damage = model.wall_damage[wall_key]
                        else:
                            damage = 1
                            
                        if damage >= 2:
                            print(f"⚡ Shockwave destroyed a wall between ({x-dx},{y-dy}) and ({x},{y})")
                            # If wall was destroyed, continue propagation
                        else:
                            print(f"⚡ Shockwave damaged a wall between ({x-dx},{y-dy}) and ({x},{y}), total damage: {damage}")
                            # If only damaged but not destroyed, stop
                            stopped = True
                            break
            
            # If we get here, it's because there was no wall or door stopping the shockwave
            # Or because we passed through a destroyed/open wall/door
            
            # Check if we're in the perimeter (where effects should not propagate)
            if DirectionHelper.is_perimeter(model, x, y):
                print(f"⚡ Shockwave reached perimeter at ({x},{y})")
                break
            
            # Check effects on current cell
            cell = model.grid_state[y, x]
            
            # Check if there's a victim in the cell
            if cell["poi"] == "v":
                cell["poi"] = None
                model.victims_lost += 1
                print(f"💀 Victim at ({x},{y}) died from the shockwave")
                
                # Update POIs in the scenario
                for i, poi in enumerate(model.scenario["pois"]):
                    if poi[0] == y and poi[1] == x:
                        model.scenario["pois"].pop(i)
                        break
            
            # Check cell state and apply effects
            if cell["fire"]:
                # If there's already fire, the shockwave continues
                print(f"⚡ Shockwave passes through cell with fire at ({x},{y})")
                # Don't stop, continue propagation
            elif cell["smoke"]:
                # If there's smoke, convert to fire and stop
                cell["smoke"] = False
                cell["fire"] = True
                if (y, x) not in model.scenario["fires"]:
                    model.scenario["fires"].append((y, x))
                print(f"⚡ Shockwave converted smoke to fire at ({x},{y}) and stopped")
                stopped = True
            else:
                # If no fire or smoke, place fire and stop
                cell["fire"] = True
                if (y, x) not in model.scenario["fires"]:
                    model.scenario["fires"].append((y, x))
                print(f"⚡ Shockwave caused fire at ({x},{y}) and stopped")
                stopped = True

    @staticmethod
    def check_firefighters_in_fire(model):
        """Checks if there are firefighters in cells with fire and sends them to ambulance"""
        rows, cols = model.grid_state.shape
        injured_firefighters = []  # List to track injured firefighters in this step
        
        # Define ambulance position in the upper right corner
        ambulance_pos = (9, 0)  # Upper right corner (x=9, y=0)
        
        # Iterate through all cells with fire
        for y in range(rows):
            for x in range(cols):
                # If there's fire in this cell
                if model.grid_state[y, x]["fire"]:
                    # Check if there are firefighters in this cell
                    cell_contents = model.grid.get_cell_list_contents((x, y))
                    firefighters = [agent for agent in cell_contents if isinstance(agent, FirefighterAgent)]
                    
                    # If there are firefighters in the cell with fire
                    for ff in firefighters:
                        # Add to injured list
                        injured_firefighters.append(ff)
                        
        # If no injured firefighters, show informative message and exit
        if not injured_firefighters:
            print("✓ No firefighters in cells with fire")
            return
        
        # Process each injured firefighter
        for ff in injured_firefighters:
            x, y = ff.pos
            print(f"🚑 FIREFIGHTER INJURED! Firefighter {ff.unique_id} is in a cell with fire ({x},{y})")
            
            # If firefighter is carrying a victim, the victim is lost
            if ff.carrying:
                ff.carrying = False
                model.victims_lost += 1
                print(f"💀 The victim carried by firefighter {ff.unique_id} perished in the fire")
                # Replenish POI when a victim is lost
                GameMechanics.replenish_pois(model)
            
            # Send firefighter to ambulance area in the upper right corner
            # First, remove firefighter from current position
            model.grid.remove_agent(ff)
            
            # Then, place in ambulance area
            model.grid.place_agent(ff, ambulance_pos)
            
            print(f"🚑 Firefighter {ff.unique_id} has been moved to ambulance area ({ambulance_pos})")
            
            # Reduce firefighter's AP to 0 to simulate not being able to take more actions this turn
            ff.ap = 0

    @staticmethod
    def replenish_pois(model):
        """Replenishes POIs on the board to always maintain 3 POIs available"""
        # 1. Count how many POIs are currently on the board
        current_pois_count = len(model.scenario["pois"])
        
        print(f"\n=== POI REPLENISHMENT ===")
        print(f"Current POIs on board: {current_pois_count}")
        
        # If there are already 3 or more POIs, do nothing
        if current_pois_count >= 3:
            print("There are already enough POIs on the board.")
            return
        
        # 2. Determine how many POIs we need to add
        pois_to_add = 3 - current_pois_count
        print(f"Need to add {pois_to_add} POIs")
        
        # 3. Initialize the POI deck if it doesn't exist
        if not hasattr(model, "mazo_pois"):
            # Count how many victims and false alarms are already in the initial scenario
            initial_victims_count = sum(1 for poi in model.scenario["pois"] if poi[2] == "v")
            initial_false_alarms_count = sum(1 for poi in model.scenario["pois"] if poi[2] == "f")
            
            # Create deck with remaining POIs (10 - X victims, 5 - Y false alarms)
            remaining_victims = 10 - initial_victims_count
            remaining_false_alarms = 5 - initial_false_alarms_count
            
            # Ensure no negative numbers
            remaining_victims = max(0, remaining_victims)
            remaining_false_alarms = max(0, remaining_false_alarms)
            
            # Create initial deck
            model.mazo_pois = ["v"] * remaining_victims + ["f"] * remaining_false_alarms
            
            # Shuffle deck
            model.random.shuffle(model.mazo_pois)
            
            print(f"POI deck initialized with {remaining_victims} victims and {remaining_false_alarms} false alarms.")
            print(f"Total in deck: {len(model.mazo_pois)} POIs")
        
        # 4. For each POI to add, select from deck and place
        for _ in range(pois_to_add):
            # Check if deck is empty
            if not model.mazo_pois:
                print("POI deck is empty. No more POIs can be added.")
                break
            
            # Draw a POI from the deck (type 'v' or 'f')
            poi_type = model.mazo_pois.pop(0)
            print(f"Drawing POI from deck: {poi_type}. {len(model.mazo_pois)} remain in deck.")
            
            # Find a valid cell to place the POI
            placed = False
            attempts = 0
            max_attempts = 100  # Limit to avoid infinite loops
            
            while not placed and attempts < max_attempts:
                attempts += 1
                
                # Generate random coordinates (outside perimeter)
                rows, cols = model.grid_state.shape
                row = model.random.randint(1, rows - 2)  # From 1 to rows-2
                col = model.random.randint(1, cols - 2)  # From 1 to cols-2
                
                # Check if cell is valid (doesn't already have a POI)
                if model.grid_state[row, col]["poi"] is None:
                    # If there's fire or smoke, remove it
                    if model.grid_state[row, col]["fire"]:
                        model.grid_state[row, col]["fire"] = False
                        # Remove from fire list if it was there
                        if (row, col) in model.scenario["fires"]:
                            model.scenario["fires"].remove((row, col))
                        print(f"Fire removed at ({col},{row}) to place a POI.")
                    
                    if model.grid_state[row, col]["smoke"]:
                        model.grid_state[row, col]["smoke"] = False
                        print(f"Smoke removed at ({col},{row}) to place a POI.")
                    
                    # Place the POI
                    model.grid_state[row, col]["poi"] = poi_type
                    model.scenario["pois"].append((row, col, poi_type))
                    
                    print(f"New POI type '{poi_type}' placed at ({col},{row})")
                    
                    # Check if there are firefighters in the cell to reveal POI immediately
                    cell_contents = model.grid.get_cell_list_contents((col, row))
                    firefighters = [agent for agent in cell_contents if isinstance(agent, FirefighterAgent)]
                    
                    if firefighters:
                        print(f"A firefighter is already in this cell! POI revealed immediately.")
                        if poi_type == "f":  # False alarm
                            model.grid_state[row, col]["poi"] = None
                            model.scenario["pois"].remove((row, col, poi_type))
                            print(f"It was a false alarm. POI removed.")
                        else:  # Victim
                            print(f"It's a victim. Firefighter can pick it up next turn.")
                    
                    placed = True
                
                # If couldn't place, will try another cell
            
            if not placed:
                print(f"Couldn't find a valid cell to place the POI after {max_attempts} attempts.")
                # Return card to deck and shuffle
                model.mazo_pois.append(poi_type)
                model.random.shuffle(model.mazo_pois)
        
        print(f"POI replenishment completed. Total POIs on board: {len(model.scenario['pois'])}")
        print(f"POIs remaining in deck: {len(model.mazo_pois)}")

    @staticmethod
    def check_end_conditions(model):
        """
        Checks if victory or defeat conditions have been met
        
        Returns:
            bool: True if game has ended, False if it continues
        """
        # 1. Check victory condition (7+ rescued victims)
        if model.victims_rescued >= 7:
            print("\n🎖️🎖️🎖️ VICTORY! 🎖️🎖️🎖️")
            print(f"The firefighter team has rescued {model.victims_rescued} victims.")
            print("The rescue operation has been a complete success.")
            model.simulation_over = True
            return True
            
        # 2. Check defeat by lost victims (4+ victims)
        elif model.victims_lost >= 4:
            print("\n💀💀💀 DEFEAT: Too many victims lost 💀💀💀")
            print(f"{model.victims_lost} victims have been lost in the fire.")
            print("The rescue operation has failed.")
            model.simulation_over = True
            return True
            
        # 3. Check defeat by structural collapse (24+ damage)
        elif model.damage_counters >= 24:
            print("\n🏚️🏚️🏚️ DEFEAT: Structural collapse 🏚️🏚️🏚️")
            print(f"The building has accumulated {model.damage_counters} damage points and has collapsed.")
            print("All remaining firefighters and victims have been trapped.")
            model.simulation_over = True
            return True
            
        # If no condition is met, game continues
        return False

class FirefighterAgent(Agent):
    """Firefighter agent that rescues victims from the fire"""
    
    def __init__(self, unique_id, model, pos):
        super().__init__(model)
        self.unique_id = unique_id
        self.ap = 4  # Action points
        self.carrying = False  # If carrying a victim
        self.assigned_entry = None  # Entry point assigned
        self.direction = None  # Direction of entry
        self.max_ap = 8  # Maximum AP that can be accumulated
    
    def extinguish_fire(self, cell_y, cell_x, type="fire"):
        """Attempts to extinguish fire or smoke in a specific cell"""
        cell = self.model.grid_state[cell_y, cell_x]
        
        # Check if there's fire or smoke in the cell
        if type == "fire" and cell["fire"]:
            # Check if there's enough AP to extinguish fire (2 AP)
            if self.ap >= 2:
                cell["fire"] = False
                # Remove from the model's fire list
                if (cell_y, cell_x) in self.model.scenario["fires"]:
                    self.model.scenario["fires"].remove((cell_y, cell_x))
                self.ap -= 2
                print(f"[Firefighter {self.unique_id}] ACTION: Extinguished fire at ({cell_x},{cell_y}). Remaining AP: {self.ap}")
                return True
            else:
                print(f"[Firefighter {self.unique_id}] Not enough AP to extinguish fire (needs 2 AP)")
                return False
        
        # Convert fire to smoke (1 AP)
        elif type == "convert" and cell["fire"]:
            if self.ap >= 1:
                cell["fire"] = False
                cell["smoke"] = True
                # Remove from the model's fire list
                if (cell_y, cell_x) in self.model.scenario["fires"]:
                    self.model.scenario["fires"].remove((cell_y, cell_x))
                self.ap -= 1
                print(f"[Firefighter {self.unique_id}] ACTION: Converted fire to smoke at ({cell_x},{cell_y}). Remaining AP: {self.ap}")
                return True
            else:
                print(f"[Firefighter {self.unique_id}] Not enough AP to convert fire to smoke (needs 1 AP)")
                return False
        
        # Remove smoke (1 AP)
        elif type == "smoke" and cell["smoke"]:
            if self.ap >= 1:
                cell["smoke"] = False
                self.ap -= 1
                print(f"[Firefighter {self.unique_id}] ACTION: Removed smoke at ({cell_x},{cell_y}). Remaining AP: {self.ap}")
                return True
            else:
                print(f"[Firefighter {self.unique_id}] Not enough AP to remove smoke (needs 1 AP)")
                return False
        
        return False
    
    def open_close_door(self, direction):
        """Opens or closes an adjacent door in the specified direction"""
        if self.ap < 1:
            print(f"[Firefighter {self.unique_id}] Not enough AP to open/close door (needs 1 AP)")
            return False
        
        # Get current coordinates
        x, y = self.pos
        
        # Check if there's a door in the direction using DirectionHelper
        if DirectionHelper.is_door(self.model, y, x, direction):
            door_pos = DirectionHelper.get_wall_key(y, x, direction)
            
            # If it exists, change its state
            if door_pos not in self.model.door_states:
                self.model.door_states[door_pos] = "closed"  # Initial state closed
            
            # Change state
            new_state = "open" if self.model.door_states[door_pos] == "closed" else "closed"
            self.model.door_states[door_pos] = new_state
            
            # Subtract AP
            self.ap -= 1
            
            # Use direction name from DirectionHelper
            direction_name = DirectionHelper.DIRECTION_NAMES[direction]
            print(f"[Firefighter {self.unique_id}] ACTION: {new_state.capitalize()} door to the {direction_name} from ({x},{y}). Remaining AP: {self.ap}")
            return True
        else:
            print(f"[Firefighter {self.unique_id}] No door to the {DirectionHelper.DIRECTION_NAMES[direction]} to open/close")
            return False
    
    def cut_wall(self, direction):
        """Cuts an adjacent wall in the specified direction"""
        if self.ap < 2:
            print(f"[Firefighter {self.unique_id}] Not enough AP to cut wall (needs 2 AP)")
            return False
        
        # Get current coordinates
        x, y = self.pos
        
        # Check if there's a wall in the specified direction
        if DirectionHelper.has_wall(self.model, y, x, direction):
            # Get coordinates of adjacent cell
            nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
            
            # Check if it's perimeter (using is_perimeter method)
            is_perimeter = DirectionHelper.is_perimeter(self.model, nx, ny)
            
            if is_perimeter:
                print(f"[Firefighter {self.unique_id}] ERROR: Cannot cut a wall of the outer perimeter")
                return False
            
            # Damage wall using DirectionHelper
            wall_destroyed = DirectionHelper.damage_wall(self.model, y, x, direction)
            self.ap -= 2
            
            # Message according to result and direction name from DirectionHelper
            direction_name = DirectionHelper.DIRECTION_NAMES[direction]
            if wall_destroyed:
                print(f"[Firefighter {self.unique_id}] ACTION: Destroyed wall to the {direction_name} from ({x},{y}). Remaining AP: {self.ap}")
            else:
                wall_key = DirectionHelper.get_wall_key(y, x, direction)
                print(f"[Firefighter {self.unique_id}] ACTION: Cut wall to the {direction_name} from ({x},{y}). Wall has {self.model.wall_damage[wall_key]} damage. Remaining AP: {self.ap}")
            
            return True
        else:
            print(f"[Firefighter {self.unique_id}] No wall to the {DirectionHelper.DIRECTION_NAMES[direction]} to cut")
            return False
    
    def step(self):
        # Start AP usage report
        print(f"\n[Firefighter {self.unique_id}] Starting turn with {self.ap} AP")
        
        # If we are in the board entry phase
        if self.model.stage == 1 and self.assigned_entry is not None:
            # Enter the board in the first step
            self.model.grid.move_agent(self, self.assigned_entry)
            print(f"[Firefighter {self.unique_id}] ACTION: Enters the board through entry {self.assigned_entry}")
            self.assigned_entry = None  # We've entered, no need to remember the entry
            return  # Exit because using the entry consumes the turn
        
        # While there are action points, allow actions
        while self.ap > 0:
            # Get current position
            x, y = self.pos  # Mesa uses (x=column, y=row)
            current_cell = self.model.grid_state[y, x]
            
            # CHECK 1: POI in current cell
            if current_cell["poi"] is not None:
                if current_cell["poi"] == "v" and not self.carrying:
                    # It's a victim and we're not already carrying another
                    self.carrying = True
                    current_cell["poi"] = None  # Remove POI from cell
                    print(f"[Firefighter {self.unique_id}] ACTION: Picked up victim at ({x},{y})")
                elif current_cell["poi"] == "f":
                    # It's a false alarm
                    current_cell["poi"] = None  # Remove POI from cell
                    print(f"[Firefighter {self.unique_id}] ACTION: Found a false alarm at ({x},{y})")
            
            # CHECK 2: Rescue at entry with victim
            if self.carrying:
                is_entry = self.pos in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                is_perimeter = self.pos[0] == 0 or self.pos[0] == self.model.grid.width - 1 or \
                            self.pos[1] == 0 or self.pos[1] == self.model.grid.height - 1
                
                if is_entry and is_perimeter:
                    print(f"[Firefighter {self.unique_id}] ACTION: RESCUE COMPLETED! Has rescued the victim at {self.pos}")
                    self.carrying = False
                    return  # The rescue consumes the turn
        
            # In a real game, the user would choose what action to perform
            possible_actions = []
            
            # 1. Can always try to move
            possible_actions.append("move")
            
            # 2. Check if can extinguish fire in current or adjacent cells
            # Get adjacent cells
            adjacent_cells = []
            for direction in range(4):
                nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
                if 0 <= ny < self.model.grid.height and 0 <= nx < self.model.grid.width:
                    # Check if we can pass through the wall in that direction
                    if DirectionHelper.can_pass_wall(self.model, y, x, direction):
                        adjacent_cells.append((ny, nx))

            # Check fire in current cell
            if current_cell["fire"] and self.ap >= 2:
                possible_actions.append("extinguish_fire")
                possible_actions.append("convert_fire_to_smoke")
            
            # Check smoke in current cell
            if current_cell["smoke"] and self.ap >= 1:
                possible_actions.append("remove_smoke")
            
            # Check fire in adjacent cells
            for cell_y, cell_x in adjacent_cells:
                if self.model.grid_state[cell_y, cell_x]["fire"] and self.ap >= 2:
                    possible_actions.append("extinguish_adjacent_fire")
                    possible_actions.append("convert_adjacent_fire_to_smoke")
                if self.model.grid_state[cell_y, cell_x]["smoke"] and self.ap >= 1:
                    possible_actions.append("remove_adjacent_smoke")
            
            # 3. Check adjacent doors to open/close
            walls = current_cell["walls"]
            for i in range(4):  # Check in 4 directions
                door_pos = None
                if i == 0 and y > 0:  # North
                    door_pos = (y, x, 0)
                elif i == 1 and x < self.model.grid.width - 1:  # East
                    door_pos = (y, x, 1)
                elif i == 2 and y < self.model.grid.height - 1:  # South
                    door_pos = (y, x, 2)
                elif i == 3 and x > 0:  # West
                    door_pos = (y, x, 3)
                
                if door_pos:
                    door_positions = ScenarioParser.compute_door_positions(self.model.scenario["doors"])
                    if door_pos in door_positions and self.ap >= 1:
                        possible_actions.append(f"door_{i}")
            
            # 4. Check walls that can be cut
            for i in range(4):
                if walls[i] == 1 and self.ap >= 2:  # There's a wall and I have enough AP
                    # More complete perimeter check
                    is_perimeter = False
                    
                    # Direct check by wall position and direction
                    if i == 0:  # North
                        if y == 1:  # The cell above would be perimeter (0)
                            is_perimeter = True
                    elif i == 1:  # East
                        if x == self.model.grid.width - 2:  # The cell to the right would be perimeter (width-1)
                            is_perimeter = True
                    elif i == 2:  # South
                        if y == self.model.grid.height - 2:  # The cell below would be perimeter (height-1)
                            is_perimeter = True
                    elif i == 3:  # West
                        if x == 1:  # The cell to the left would be perimeter (0)
                            is_perimeter = True
                            
                    # Also check if current cell is perimeter and direction goes outward
                    if (y == 0 and i == 0) or \
                    (x == self.model.grid.width - 1 and i == 1) or \
                    (y == self.model.grid.height - 1 and i == 2) or \
                    (x == 0 and i == 3):
                        is_perimeter = True
                        
                    if not is_perimeter:
                        possible_actions.append(f"cut_{i}")
            
            # 5. Can always pass turn
            # Check if in ambulance position
            is_ambulance = (x == 9 and y == 0)
            
            # If no possible actions OR
            # has 4 or fewer AP (to optimize) OR
            # is in the ambulance
            if (len(possible_actions) == 0) or (self.ap <= 4) or is_ambulance:
                possible_actions.append("pass")
                
            # Choose action randomly (for simulation)
            action = self.model.random.choice(possible_actions)
            
            # Execute chosen action
            if action == "move":
                # Existing movement logic
                self._perform_movement()
            elif action == "extinguish_fire":
                self.extinguish_fire(y, x, "fire")
            elif action == "convert_fire_to_smoke":
                self.extinguish_fire(y, x, "convert")
            elif action == "remove_smoke":
                self.extinguish_fire(y, x, "smoke")
            elif action == "extinguish_adjacent_fire":
                # Choose an adjacent cell with fire randomly
                cells_with_fire = [(cy, cx) for cy, cx in adjacent_cells 
                                 if self.model.grid_state[cy, cx]["fire"]]
                if cells_with_fire:
                    cy, cx = self.model.random.choice(cells_with_fire)
                    self.extinguish_fire(cy, cx, "fire")
            elif action == "convert_adjacent_fire_to_smoke":
                # Choose an adjacent cell with fire randomly
                cells_with_fire = [(cy, cx) for cy, cx in adjacent_cells 
                                 if self.model.grid_state[cy, cx]["fire"]]
                if cells_with_fire:
                    cy, cx = self.model.random.choice(cells_with_fire)
                    self.extinguish_fire(cy, cx, "convert")
            elif action == "remove_adjacent_smoke":
                # Choose an adjacent cell with smoke randomly
                cells_with_smoke = [(cy, cx) for cy, cx in adjacent_cells 
                                  if self.model.grid_state[cy, cx]["smoke"]]
                if cells_with_smoke:
                    cy, cx = self.model.random.choice(cells_with_smoke)
                    self.extinguish_fire(cy, cx, "smoke")
            elif action.startswith("door_"):
                direction = int(action.split("_")[1])
                self.open_close_door(direction)
            elif action.startswith("cut_"):
                direction = int(action.split("_")[1])
                self.cut_wall(direction)
            elif action == "pass":
                print(f"[Firefighter {self.unique_id}] ACTION: Passes turn. Remaining AP: {self.ap}")
                # End turn
                break
        
        # Turn summary
        print(f"[Firefighter {self.unique_id}] Ends turn. Current position: {self.pos}, Carrying victim: {self.carrying}")
    
    def _perform_movement(self):
        """Helper method to perform a movement, respecting constraints"""
        # Get current position
        x, y = self.pos
        
        # List of possible movements
        movements = []
        
        # Check all 4 directions
        for direction in range(4):
            # Check if we can pass in this direction
            if DirectionHelper.can_pass_wall(self.model, y, x, direction):
                # Get coordinates of adjacent cell
                nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
                
                # Check if within limits
                if 0 <= ny < self.model.grid.height and 0 <= nx < self.model.grid.width:
                    # Check additional restrictions
                    dest_cell = self.model.grid_state[ny, nx]
                    
                    # Check if it's perimeter
                    is_perimeter = DirectionHelper.is_perimeter(self.model, nx, ny)
                    
                    # Check if it's an entry
                    is_entry = DirectionHelper.is_entry(self.model, nx, ny)
                    
                    # CORRECTION: Calculate AP cost for this movement
                    ap_cost = 1  # By default, moving costs 1 AP
                    
                    # CORRECTED: If destination cell has FIRE (not smoke), costs 2 AP
                    if dest_cell["fire"]:
                        ap_cost = 2
                    
                    # If carrying a victim, costs 2 AP
                    if self.carrying:
                        ap_cost = 2
                    
                    # Don't go to cells with fire if carrying victim
                    can_go = True
                    if self.carrying and dest_cell["fire"]:
                        can_go = False
                    
                    # Check if enough AP for this movement
                    if self.ap < ap_cost:
                        can_go = False
                    
                    # Add valid movement
                    if can_go and (not is_perimeter or (self.carrying and is_entry)):
                        # Save both position and AP cost
                        movements.append((nx, ny, ap_cost))
        
        # If no valid movements, end turn
        if not movements:
            print(f"[Firefighter {self.unique_id}] ACTION: Cannot move from {self.pos}, Remaining AP: {self.ap}")
            # Additional debug info when cannot move with victim
            if self.carrying:
                print(f"[Debug] Firefighter {self.unique_id} is carrying a victim but cannot move. Possible reasons:")
                print(f"  - All adjacent cells have fire")
                print(f"  - No accessible entries nearby")
            return False
        
        # Choose a random direction
        new_pos_info = self.model.random.choice(movements)
        new_pos = (new_pos_info[0], new_pos_info[1])  # Extract only x,y coordinates
        ap_cost = new_pos_info[2]  # Extract AP cost separately
        
        # Check if movement is towards an entry while carrying victim
        is_entry = new_pos in [(e[1], e[0]) for e in self.model.scenario["entries"]]
        is_perimeter = new_pos[0] == 0 or new_pos[0] == self.model.grid.width - 1 or \
                     new_pos[1] == 0 or new_pos[1] == self.model.grid.height - 1
        
        # Move agent with only x,y coordinates
        self.model.grid.move_agent(self, new_pos)
        
        # NEW: Subtract corresponding AP cost
        self.ap -= ap_cost
        
        # Generate message based on movement type
        if self.carrying and is_entry and is_perimeter:
            print(f"[Firefighter {self.unique_id}] ACTION: RESCUE COMPLETED! Exited through entry {new_pos} with victim. Remaining AP: {self.ap}")
            self.carrying = False  # No longer carrying victim
            self.model.victims_rescued += 1  # Increment rescued victims counter
            
            # New: Call replenish_pois to immediately replenish
            GameMechanics.replenish_pois(self.model)
            
            return True
        else:
            print(f"[Firefighter {self.unique_id}] ACTION: Moved to {new_pos}. Remaining AP: {self.ap}")
            
            # Check POI in new position
            new_x, new_y = new_pos
            new_cell = self.model.grid_state[new_y, new_x]
            
            # If there's a POI in the new cell
            if new_cell["poi"] is not None:
                # Save POI type before removing it
                poi_type = new_cell["poi"]
                
                if poi_type == "v" and not self.carrying:
                    # It's a victim and we're not already carrying another
                    self.carrying = True
                    new_cell["poi"] = None  # Remove POI from cell
                    
                    # Remove POI from scenario's POI list
                    for i, poi in enumerate(self.model.scenario["pois"]):
                        if poi[0] == new_y and poi[1] == new_x:
                            self.model.scenario["pois"].pop(i)
                            break
                    
                    print(f"[Firefighter {self.unique_id}] ACTION: Picked up victim at ({new_x},{new_y})")
                
                elif poi_type == "f":
                    # It's a false alarm
                    new_cell["poi"] = None  # Remove POI from cell
                    
                    # Remove POI from scenario's POI list
                    for i, poi in enumerate(self.model.scenario["pois"]):
                        if poi[0] == new_y and poi[1] == new_x:
                            self.model.scenario["pois"].pop(i)
                            break
                    
                    print(f"[Firefighter {self.unique_id}] ACTION: Found a false alarm at ({new_x},{new_y})")
                    
                    # New: Replenish POI after discovering false alarm
                    GameMechanics.replenish_pois(self.model)
            
            return True

class FireRescueModel(Model):
    """Fire rescue simulation model"""
    
    def __init__(self, scenario):
        super().__init__()
        
        # Configure the space (width=10, height=8)
        self.grid = MultiGrid(10, 8, False)  # Changed from SingleGrid to MultiGrid
        
        # Configure scheduler with random activation
        self.schedule = RandomActivation(self)
        
        # Store scenario and grid state
        self.scenario = scenario
        self.grid_state = ScenarioParser.build_grid_state(scenario)
        
        # NEW: Registers for new mechanics
        self.door_states = {}  # Dictionary for door states (open/closed)
        
        # Initialize all doors as closed
        door_positions = ScenarioParser.compute_door_positions(scenario["doors"])
        for door_pos in door_positions:
            self.door_states[door_pos] = "closed"
        
        self.wall_damage = {}  # Dictionary for wall damage
        
        # NEW: Game counters
        self.victims_lost = 0      # Victims lost to fire
        self.victims_rescued = 0   # Victims rescued by firefighters
        self.damage_counters = 0   # Total damage markers placed
        
        # NEW: Simulation end control variable
        self.simulation_over = False
        
        # Place firefighters outside the board, near entries
        self.create_agents()
        
        # Counter to track number of steps
        self.step_count = 0
        
        # Stage: 0=initial (firefighters outside), 1=firefighters entering, 2+=normal simulation
        self.stage = 0
    
    def create_agents(self):
        """Create 6 firefighter agents distributed among available entries"""
        # Total number of firefighters to create
        num_firefighters = 6
        
        # Number of available entries
        num_entries = len(self.scenario["entries"])
        
        for i in range(num_firefighters):
            # Select entry cyclically (0, 1, 2, 3, 0, 1)
            entry_idx = i % num_entries
            pos = self.scenario["entries"][entry_idx]
            
            # Determine entry direction and external position
            row, column = pos
            
            # Determine which border is closest to place the firefighter outside
            rows, columns = self.grid_state.shape
            north_dist = row
            south_dist = rows - 1 - row
            west_dist = column
            east_dist = columns - 1 - column
            
            # Determine external coordinates based on closest direction
            if north_dist <= min(south_dist, west_dist, east_dist):
                # Entry from north, firefighter above the entry
                ext_row, ext_col = row - 1, column
                direction = "north"
            elif south_dist <= min(north_dist, west_dist, east_dist):
                # Entry from south, firefighter below the entry
                ext_row, ext_col = row + 1, column
                direction = "south"
            elif west_dist <= min(north_dist, south_dist, east_dist):
                # Entry from west, firefighter to the left of the entry
                ext_row, ext_col = row, column - 1
                direction = "west"
            else:
                # Entry from east, firefighter to the right of the entry
                ext_row, ext_col = row, column + 1
                direction = "east"
            
            # Create external position for Mesa (x=column, y=row)
            mesa_ext_pos = (ext_col, ext_row)
            
            # Create agent
            agent = FirefighterAgent(i, self, mesa_ext_pos)
            agent.assigned_entry = (column, row)  # Save assigned entry
            agent.direction = direction  # Save direction
            
            # IMPORTANT: Register agent in the grid for visualization
            try:
                self.grid.place_agent(agent, mesa_ext_pos)
                print(f"Firefighter {i} placed at {mesa_ext_pos}, will enter through entry {entry_idx+1} ({column},{row})")
            except Exception as e:
                # If it fails, register it in the nearest valid cell
                print(f"Could not place firefighter at {mesa_ext_pos}: {e}")
                # Use entry position as alternative
                self.grid.place_agent(agent, (column, row))
                print(f"Firefighter {i} placed at entry {column, row}")
                
            self.schedule.add(agent)
    
    def step(self):
        """Advance simulation one step"""
        # Check if simulation has already ended
        if self.simulation_over:
            print("The simulation has ended. No more steps can be executed.")
            return
                    
        self.step_count += 1

        # FIRST: Display step info
        if self.stage == 0:
            print(f"\n--- Step {self.step_count}: Firefighters entering the board ---")
            self.stage = 1
        else:
            print(f"\n--- Step {self.step_count} ---")

        # SECOND: Execute each agent's step
        self.schedule.step()

        # THIRD: Propagate fire AFTER all agents have acted (pero no en el primer turno)
        if self.step_count > 1:  # No propagar fuego en el step 1
            print("\n=== FIRE PROPAGATION ===")
            GameMechanics.advance_fire(self)

            # FOURTH: Apply secondary effects (e.g., firefighters in fire)
            print("\n=== CHECKING FIREFIGHTERS IN FIRE ===")
            GameMechanics.check_firefighters_in_fire(self)
        else:
            print("\n=== FIRE PROPAGATION SKIPPED (FIRST TURN) ===")
            print("Fire propagation will start from the next turn")

        # FIFTH: Replenish POIs at the end of the turn
        GameMechanics.replenish_pois(self)

        # SIXTH: Restore AP for all firefighters
        for agent in self.schedule.agents:
            # Accumulate AP without exceeding maximum
            agent.ap = min(agent.ap + 4, agent.max_ap)

        # SEVENTH: Check game end conditions
        GameMechanics.check_end_conditions(self)

        # EIGHTH: Print turn summary
        print("\n==== End of turn ====")
        print(f"Rescued victims: {self.victims_rescued}")
        print(f"Lost victims: {self.victims_lost}")
        print(f"Accumulated wall damage: {self.damage_counters}")
        print(f"POIs on board: {len(self.scenario['pois'])}")

        # NINTH: Visualize updated game state
        print("\n=== UPDATED SIMULATION STATE ===")
        plt.figure(figsize=(12, 10))
        Visualization.visualize_grid_with_perimeter_and_doors(
            self.scenario["grid_walls"], 
            ScenarioParser.compute_door_positions(self.scenario["doors"]), 
            self.scenario["entries"],
            self.scenario["fires"],   
            self.scenario["pois"],
            self
        )
        plt.show()


class Visualization:
    """Class that encapsulates all visualization functionalities"""
    
    @staticmethod
    def visualize_grid_with_perimeter_and_doors(grid, door_positions, entries, fires=None, pois=None, model=None):
        """Visualizes the game board with all its elements"""
        rows, columns = grid.shape[:2]
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_facecolor('#d9f2d9')  # Light green background

        # Determine the direction of each entry (towards the nearest edge)
        entry_positions = []
        for y, x in entries:
            # Determine which edge is closest
            north_dist = y
            south_dist = rows - 1 - y
            west_dist = x
            east_dist = columns - 1 - x
            
            # The direction with minimum distance is closest to the edge
            min_dist = min(north_dist, south_dist, west_dist, east_dist)
            
            if min_dist == north_dist:
                entry_positions.append((y, x, 0))  # North
            elif min_dist == east_dist:
                entry_positions.append((y, x, 1))  # East
            elif min_dist == south_dist:
                entry_positions.append((y, x, 2))  # South
            else:  # min_dist == west_dist
                entry_positions.append((y, x, 3))  # West

        for y in range(rows):
            for x in range(columns):
                # Check if there's fire or smoke in this cell
                is_fire = (y, x) in fires if fires else False
                is_smoke = False
                
                if model is not None:
                    # Use grid_state to detect smoke
                    is_smoke = model.grid_state[y, x]["smoke"]
                
                # Determine background color based on the cell
                if is_fire:
                    color = '#ffcccc'  # Light reddish color for fire
                elif is_smoke:
                    color = '#e6e6e6'  # Light gray color for smoke
                elif x == 0 or x == columns-1 or y == 0 or y == rows-1:
                    color = '#b3e6b3'  # Light green color for perimeter
                else:
                    color = '#e6f7ff'  # Light blue color for playable cells
                    
                rect = patches.Rectangle((x, rows - y - 1), 1, 1, linewidth=0, facecolor=color)
                ax.add_patch(rect)

                # Draw light grid lines
                ax.plot([x, x+1], [rows - y - 1, rows - y - 1], color='gray', linewidth=0.3)
                ax.plot([x, x+1], [rows - y, rows - y], color='gray', linewidth=0.3)
                ax.plot([x, x], [rows - y - 1, rows - y], color='gray', linewidth=0.3)
                ax.plot([x+1, x+1], [rows - y - 1, rows - y], color='gray', linewidth=0.3)

                # Draw symbols for fire if applicable
                if is_fire:
                    ax.plot(x + 0.5, rows - y - 0.5, 'o', markersize=15, 
                            markerfacecolor='#ff6600', markeredgecolor='red', alpha=0.7)
                    ax.plot(x + 0.5, rows - y - 0.5, '*', markersize=10, 
                            markerfacecolor='yellow', markeredgecolor='yellow')
                
                # Draw symbols for smoke if applicable
                elif is_smoke:
                    ax.plot(x + 0.5, rows - y - 0.5, 's', markersize=14, 
                            markerfacecolor='#a6a6a6', markeredgecolor='#808080', alpha=0.6)
                    ax.plot(x + 0.5, rows - y - 0.5, 'o', markersize=8, 
                            markerfacecolor='#d3d3d3', markeredgecolor='#d3d3d3', alpha=0.8)

                # Check if there's a POI in this position
                if pois:
                    for poi_y, poi_x, poi_type in pois:
                        if poi_y == y and poi_x == x:
                            if poi_type == 'v':  # Victim
                                ax.plot(x + 0.5, rows - y - 0.5, 'D', markersize=12, 
                                        markerfacecolor='#00cc66', markeredgecolor='black', zorder=10)
                            elif poi_type == 'f':  # False alarm
                                ax.plot(x + 0.5, rows - y - 0.5, 'X', markersize=12, 
                                        markerfacecolor='#cccccc', markeredgecolor='black', zorder=10)
                                
                # Determine if it's a perimeter cell
                is_perimeter = (x == 0 or x == columns-1 or y == 0 or y == rows-1)

                if is_perimeter:
                    # Only draw outer perimeter walls
                    if y == 0:
                        ax.plot([x, x+1], [rows - y, rows - y], color='black', linewidth=2.5)
                    if y == rows-1:
                        ax.plot([x, x+1], [rows - y - 1, rows - y - 1], color='black', linewidth=2.5)
                    if x == 0:
                        ax.plot([x, x], [rows - y - 1, rows - y], color='black', linewidth=2.5)
                    if x == columns-1:
                        ax.plot([x+1, x+1], [rows - y - 1, rows - y], color='black', linewidth=2.5)
                else:
                    # CHANGE: Use grid_state instead of grid for walls
                    if model is not None:
                        wall_n, wall_e, wall_s, wall_w = model.grid_state[y, x]["walls"]
                    else:
                        wall_n, wall_e, wall_s, wall_w = grid[y, x]

                    # Check if there's a door or entry in each direction
                    door_n = (y, x, 0) in door_positions
                    door_e = (y, x, 1) in door_positions
                    door_s = (y, x, 2) in door_positions
                    door_w = (y, x, 3) in door_positions
                    
                    entry_n = (y, x, 0) in entry_positions
                    entry_e = (y, x, 1) in entry_positions
                    entry_s = (y, x, 2) in entry_positions
                    entry_w = (y, x, 3) in entry_positions

                    # Draw walls, doors or entries as appropriate
                    if entry_n:
                        # Draw north entry
                        ax.plot([x+0.25, x+0.75], [rows - y, rows - y], color='white', linewidth=4.0)
                    elif door_n:
                        # Draw north door according to its state
                        door_color = 'brown'
                        door_open = False
                        if model is not None and (y, x, 0) in model.door_states:
                            door_open = model.door_states[(y, x, 0)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        else:
                            # If not in door_states but is a door, it's considered destroyed
                            if model is not None:
                                door_color = 'lightgreen'  # Distinctive color for destroyed doors
                        ax.plot([x+0.25, x+0.75], [rows - y, rows - y], color=door_color, linewidth=2.5)
                    elif wall_n:
                        # Draw north wall
                        wall_color = 'black'
                        if model is not None and (y, x, 0) in model.wall_damage:
                            # If the wall has damage, change color
                            if model.wall_damage[(y, x, 0)] == 1:
                                wall_color = 'orange'  # Wall damaged once
                            # If it has 2 damages, don't draw it (it's destroyed)
                            elif model.wall_damage[(y, x, 0)] >= 2:
                                wall_color = None  # Don't draw
                        
                        if wall_color:
                            ax.plot([x, x+1], [rows - y, rows - y], color=wall_color, linewidth=2.5)
                    
                    # For doors in East direction:
                    if entry_e:
                        # Draw east entry
                        ax.plot([x+1, x+1], [rows - y - 0.75, rows - y - 0.25], color='white', linewidth=4.0)
                    elif door_e:
                        # Draw east door according to its state
                        door_color = 'brown'
                        if model is not None and (y, x, 1) in model.door_states:
                            door_open = model.door_states[(y, x, 1)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        else:
                            # If not in door_states but is a door, it's considered destroyed
                            if model is not None:
                                door_color = 'lightgreen'  # Distinctive color for destroyed doors
                        ax.plot([x+1, x+1], [rows - y - 0.75, rows - y - 0.25], color=door_color, linewidth=2.5)
                    elif wall_e:
                        # Draw east wall
                        wall_color = 'black'
                        if model is not None and (y, x, 1) in model.wall_damage:
                            # If the wall has damage, change color
                            if model.wall_damage[(y, x, 1)] == 1:
                                wall_color = 'orange'
                            elif model.wall_damage[(y, x, 1)] >= 2:
                                wall_color = None
                        
                        if wall_color:
                            ax.plot([x+1, x+1], [rows - y - 1, rows - y], color=wall_color, linewidth=2.5)
                    
                    # For doors in South direction:
                    if entry_s:
                        # Draw south entry
                        ax.plot([x+0.25, x+0.75], [rows - y - 1, rows - y - 1], color='white', linewidth=4.0)
                    elif door_s:
                        # Draw south door according to its state
                        door_color = 'brown'
                        if model is not None and (y, x, 2) in model.door_states:
                            door_open = model.door_states[(y, x, 2)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        else:
                            # If not in door_states but is a door, it's considered destroyed
                            if model is not None:
                                door_color = 'lightgreen'  # Distinctive color for destroyed doors
                        ax.plot([x+0.25, x+0.75], [rows - y - 1, rows - y - 1], color=door_color, linewidth=2.5)
                    elif wall_s:
                        # Draw south wall
                        wall_color = 'black'
                        if model is not None and (y, x, 2) in model.wall_damage:
                            # If the wall has damage, change color
                            if model.wall_damage[(y, x, 2)] == 1:
                                wall_color = 'orange'
                            elif model.wall_damage[(y, x, 2)] >= 2:
                                wall_color = None
                        
                        if wall_color:
                            ax.plot([x, x+1], [rows - y - 1, rows - y - 1], color=wall_color, linewidth=2.5)
                    
                    if entry_w:
                        # Draw west entry
                        ax.plot([x, x], [rows - y - 0.75, rows - y - 0.25], color='white', linewidth=4.0)
                    elif door_w:
                        # Draw west door according to its state
                        door_color = 'brown'
                        if model is not None and (y, x, 3) in model.door_states:
                            door_open = model.door_states[(y, x, 3)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        else:
                            # If not in door_states but is a door, it's considered destroyed
                            if model is not None:
                                door_color = 'lightgreen'  # Distinctive color for destroyed doors
                        ax.plot([x, x], [rows - y - 0.75, rows - y - 0.25], color=door_color, linewidth=2.5)
                    elif wall_w:
                        # Draw west wall
                        wall_color = 'black'
                        if model is not None and (y, x, 3) in model.wall_damage:
                            # If the wall has damage, change color
                            if model.wall_damage[(y, x, 3)] == 1:
                                wall_color = 'orange'
                            elif model.wall_damage[(y, x, 3)] >= 2:
                                wall_color = None
                        
                        if wall_color:
                            ax.plot([x, x], [rows - y - 1, rows - y], color=wall_color, linewidth=2.5)
                        
        # Add elements to the legend
        entry_line = plt.Line2D([0], [0], color='white', linewidth=4.0, label='Firefighter entry')
        perimeter_patch = patches.Patch(color='#b3e6b3', label='Perimeter')
        playable_patch = patches.Patch(color='#e6f7ff', label='Playable cell')
        door_line = plt.Line2D([0], [0], color='brown', linewidth=2.5, label='Door')
        wall_line = plt.Line2D([0], [0], color='black', linewidth=2.5, label='Wall')
        
        # New elements for the legend
        fire_marker = plt.Line2D([0], [0], marker='o', markersize=15, markerfacecolor='#ff6600', 
                                markeredgecolor='red', alpha=0.7, linestyle='', label='Fire')
        smoke_marker = plt.Line2D([0], [0], marker='s', markersize=14, markerfacecolor='#a6a6a6', 
                                markeredgecolor='#808080', alpha=0.6, linestyle='', label='Smoke')
        victim_marker = plt.Line2D([0], [0], marker='D', markersize=12, markerfacecolor='#00cc66', 
                                markeredgecolor='black', linestyle='', label='Victim (POI)')
        false_alarm_marker = plt.Line2D([0], [0], marker='X', markersize=12, markerfacecolor='#cccccc', 
                                markeredgecolor='black', linestyle='', label='False alarm (POI)')
        
        ax.legend(handles=[perimeter_patch, playable_patch, entry_line, wall_line, door_line, 
                        fire_marker, smoke_marker, victim_marker, false_alarm_marker], 
                loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)

        if model is not None:
            # Add firefighters to the legend
            firefighter_marker = plt.Line2D([0], [0], marker='o', markersize=15, 
                                      markerfacecolor='blue', markeredgecolor='navy', 
                                      alpha=0.7, linestyle='', label='Firefighter')
            
            # Update the legend to include firefighters
            ax.legend(handles=[perimeter_patch, playable_patch, entry_line, wall_line, 
                              door_line, fire_marker, victim_marker, false_alarm_marker,
                              firefighter_marker], 
                      loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
            
            # Configure limits to see ALL the area, including exterior
            ax.set_xlim(-1, columns+1) 
            ax.set_ylim(-1, rows+1)
            
            # Draw firefighters as blue circles with ID number
            for agent in model.schedule.agents:
                x, y = agent.pos  # Mesa uses (x=column, y=row)
                # Draw firefighters with adjusted coordinates
                ax.plot(x + 0.5, rows - y - 0.5, 'o', markersize=24, 
                        markerfacecolor='blue', markeredgecolor='navy', alpha=0.7, zorder=25)
                ax.text(x + 0.5, rows - y - 0.5, str(agent.unique_id), color='white', 
                        fontsize=12, ha='center', va='center', zorder=26)
            
            # Update title if there's a model
            ax.set_title(f"Simulation - Step {model.step_count}")
        
        # Visual aspect 
        ax.set_xticks(range(columns))
        ax.set_yticks(range(rows))
        ax.set_xticklabels(range(columns))
        ax.set_yticklabels(range(rows - 1, -1, -1))
        ax.set_aspect('equal')
        
        # IMPORTANT: Update title to reflect current step
        if model is not None:
            ax.set_title(f"Simulation - Step {model.step_count}")
        else:
            ax.set_title("6×8 Scenario Map with Perimeter (8×10), Walls and Doors")
        
        ax.grid(False)
        plt.tight_layout()
        return fig, ax

    @staticmethod
    def visualize_simulation(model):
        """Visualizes the current state of the simulation, including firefighters"""
        # Reuse the base grid visualization
        fig, ax = Visualization.visualize_grid_with_perimeter_and_doors(
            model.scenario["grid_walls"], 
            ScenarioParser.compute_door_positions(model.scenario["doors"]), 
            model.scenario["entries"],
            model.scenario["fires"],   
            model.scenario["pois"],
            model  
        )
        plt.show()


# Parse the complete scenario
scenario = ScenarioParser.parse_scenario(scenario_content)

# Calculate door positions for visualization
door_positions = ScenarioParser.compute_door_positions(scenario["doors"])

# Show final map with doors
Visualization.visualize_grid_with_perimeter_and_doors(
    scenario["grid_walls"], 
    door_positions, 
    scenario["entries"],
    scenario["fires"],   
    scenario["pois"]      
)

# Build the grid state
print("\n=== BUILDING GRID STATE ===")
grid_state = ScenarioParser.build_grid_state(scenario)


# Additional information
print("\nScenario summary and grid state:")
print(f"Grid dimensions: {scenario['grid_walls'].shape}")
print(f"Number of POIs: {len(scenario['pois'])}")
print(f"Number of initial fires: {len(scenario['fires'])}")
print(f"Number of doors: {len(scenario['doors'])}")
print(f"Number of entries: {len(scenario['entries'])}")


print("\n=== STARTING SIMULATION ===")

# Initialize the model with our scenario
model = FireRescueModel(scenario)

# Show initial state only once
print("\n=== SIMULATION IN PROGRESS ===")
print("\n--- Initial state ---")

# Only show initial visualization
plt.figure(figsize=(12, 10))
Visualization.visualize_grid_with_perimeter_and_doors(
    scenario["grid_walls"], 
    door_positions, 
    scenario["entries"],
    scenario["fires"],   
    scenario["pois"],
    model
)
plt.show()

# Continuous simulation until victory or defeat
step = 1
while not model.simulation_over:
    model.step()  # Execute step (includes visualization at the end)
    step += 1

print("\n=== SIMULATION FINISHED ===")
print(f"Total steps executed: {step-1}")
print(f"Victims rescued: {model.victims_rescued}")
print(f"Victims lost: {model.victims_lost}")
print(f"Accumulated wall damage: {model.damage_counters}")