from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid  
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
import os

class JSONExporter:
    """Class to export game state to JSON files for Unity"""
    
    def __init__(self, output_dir="game_data"):
        self.frame_counter = 0
        self.output_dir = output_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def save_frame(self, data):
        """Saves a frame as a JSON file"""
        filename = os.path.join(self.output_dir, f"frame_{self.frame_counter:04d}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.frame_counter += 1
        return data
    
    def initial_state(self, model):
        """Generates the JSON for the initial game state"""
        firefighters = []
        for agent in model.schedule.agents:
            x, y = agent.pos
            firefighters.append({
                "id": agent.unique_id,
                "x": x,
                "y": y,
                "ap": agent.ap,
                "carrying": agent.carrying
            })
        
        cells = []
        for y in range(model.grid.height):
            for x in range(model.grid.width):
                if x < model.grid_state.shape[1] and y < model.grid_state.shape[0]:
                    cell = model.grid_state[y, x]
                    cell_json = {
                        "x": x,
                        "y": y,
                        "walls": [bool(wall) for wall in cell["walls"]],
                        "door": cell["door"],
                        "fire": cell["fire"],
                        "smoke": cell["smoke"],
                        "poi": cell["poi"]
                    }
                    cells.append(cell_json)
        
        doors = []
        door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
        for (r1, c1), (r2, c2) in model.scenario["doors"]:
            door_state = "closed"
            for pos in door_positions:
                if pos in model.door_states:
                    door_state = model.door_states[pos]
            
            doors.append({
                "from": [c1, r1],
                "to": [c2, r2],
                "state": door_state
            })
        
        pois = []
        for y, x, poi_type in model.scenario["pois"]:
            pois.append({
                "x": x,
                "y": y,
                "type": poi_type
            })
        
        entries = [[x, y] for y, x in model.scenario["entries"]]
        
        data = {
            "frame": 0,
            "turn": 0,
            "action": {
                "type": "initial_state"
            },
            "firefighters": firefighters,
            "grid": {
                "width": model.grid.width,
                "height": model.grid.height,
                "cells": cells
            },
            "doors": doors,
            "pois": pois,
            "entries": entries,
            "wall_damage": [],
            "summary": {
                "rescued": 0,
                "lost": 0,
                "damage": 0,
                "pois_in_deck": len(model.mazo_pois) if hasattr(model, "mazo_pois") else 15
            }
        }
        
        return self.save_frame(data)
    
    def action_frame(self, model, firefighter_id, action_type, **kwargs):
        """Generates the JSON for an individual action"""
        agent = None
        for a in model.schedule.agents:
            if a.unique_id == firefighter_id:
                agent = a
                break
        
        if not agent:
            return None
        
        x, y = agent.pos
        
        data = {
            "frame": self.frame_counter,
            "turn": model.step_count,
            "action": {
                "firefighter_id": firefighter_id,
                "type": action_type,
                "ap_before": kwargs.get("ap_before", 0),
                "ap_after": kwargs.get("ap_after", 0)
            },
            "firefighters": [
                {
                    "id": firefighter_id,
                    "x": x,
                    "y": y,
                    "ap": agent.ap,
                    "carrying": agent.carrying
                }
            ],
            "grid_changes": kwargs.get("grid_changes", []),
            "wall_damage": kwargs.get("wall_damage", []),
            "doors": kwargs.get("doors", []),
            "pois": kwargs.get("pois", [])
        }
        
        if action_type == "move":
            data["action"]["from"] = kwargs.get("from_pos", [0, 0])
            data["action"]["to"] = kwargs.get("to", [x, y])
        elif action_type in ["extinguish_fire", "convert_to_smoke", "remove_smoke"]:
            data["action"]["target"] = kwargs.get("target", [0, 0])
        elif action_type == "pickup_poi":
            data["action"]["target"] = kwargs.get("target", [0, 0])
            data["action"]["poi_type"] = kwargs.get("poi_type", "")
        
        return self.save_frame(data)
    
    def end_of_turn(self, model, grid_changes=None):
        """Generates the JSON for the end of turn"""
        firefighters = []
        for agent in model.schedule.agents:
            x, y = agent.pos
            firefighters.append({
                "id": agent.unique_id,
                "x": x,
                "y": y,
                "ap": agent.ap,
                "carrying": agent.carrying
            })
        
        if grid_changes is None:
            grid_changes = []
        
        pois = []
        for y, x, poi_type in model.scenario["pois"]:
            pois.append({
                "x": x,
                "y": y,
                "type": poi_type
            })
        
        data = {
            "frame": self.frame_counter,
            "turn": model.step_count,
            "action": {
                "type": "end_of_turn"
            },
            "firefighters": firefighters,
            "grid_changes": grid_changes,
            "wall_damage": [],
            "doors": [],
            "pois": pois,
            "summary": {
                "rescued": model.victims_rescued,
                "lost": model.victims_lost,
                "damage": model.damage_counters,
                "pois_in_deck": len(model.mazo_pois) if hasattr(model, "mazo_pois") else 0
            }
        }
        
        return self.save_frame(data)
    
    def game_over(self, model, result, message):
        """Generates the JSON for game over"""
        data = {
            "frame": self.frame_counter,
            "turn": model.step_count,
            "action": {
                "type": "game_over",
                "result": result,
                "message": message
            },
            "summary": {
                "rescued": model.victims_rescued,
                "lost": model.victims_lost,
                "damage": model.damage_counters
            }
        }
        
        return self.save_frame(data)

# Scenario content (full format)
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
        
        grid = np.zeros((8, 10, 4), dtype=int)

        grid[1:7, 1:9] = original_grid

        grid[0, 1:9, 0] = 1  
        grid[7, 1:9, 2] = 1  
        grid[1:7, 0, 3] = 1  
        grid[1:7, 9, 1] = 1  
        
        print("Walls parsed correctly.")
        return grid

    @staticmethod
    def _parse_pois(lines):
        """Parses the Points of Interest (POI) lines"""
        pois = []
        poi_lines = lines[6:9]  
        
        for line in poi_lines:
            parts = line.strip().split()
            if len(parts) == 3:
                row, col, poi_type = parts
                row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
                pois.append((row_idx, col_idx, poi_type))
        
        print(f"POIs parsed: {pois}")
        return pois

    @staticmethod
    def _parse_fires(lines):
        """Parses the initial fire lines"""
        fires = []
        fire_lines = lines[9:19]  
        
        for line in fire_lines:
            parts = line.strip().split()
            if len(parts) == 2:
                row, col = parts
                row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
                fires.append((row_idx, col_idx))
        
        print(f"Initial fires parsed: {fires}")
        return fires

    @staticmethod
    def _parse_doors(lines):
        """Parses the door lines"""
        doors = []
        door_lines = lines[19:27]  
        
        for line in door_lines:
            parts = line.strip().split()
            if len(parts) == 4:
                r1, c1, r2, c2 = parts
                r1_idx, c1_idx = int(r1) - 1 + 1, int(c1) - 1 + 1
                r2_idx, c2_idx = int(r2) - 1 + 1, int(c2) - 1 + 1
                doors.append(((r1_idx, c1_idx), (r2_idx, c2_idx)))
        
        print(f"Doors parsed: {doors}")
        return doors

    @staticmethod
    def _parse_entries(lines):
        """Parses the firefighter entry lines"""
        entries = []
        entry_lines = lines[27:31]  
        
        for line in entry_lines:
            parts = line.strip().split()
            if len(parts) == 2:
                row, col = parts
                row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
                entries.append((row_idx, col_idx))
        
        print(f"Entries parsed: {entries}")
        return entries

    @staticmethod
    def parse_scenario(scenario_text):
        """Main function that parses the entire scenario content"""
        lines = scenario_text.strip().split('\n')
        
        if len(lines) < 31:
            print(f"Error: The scenario must have at least 31 lines, it has {len(lines)}")
            return None
        
        grid = ScenarioParser._parse_grid_walls(lines)
        pois = ScenarioParser._parse_pois(lines)
        fires = ScenarioParser._parse_fires(lines)
        doors = ScenarioParser._parse_doors(lines)
        entries = ScenarioParser._parse_entries(lines)
        
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
            if r1 == r2:  
                if c1 < c2:  
                    door_positions.append((r1, c1, 1))  
                else:
                    door_positions.append((r1, c2, 1))  
            else:  
                if r1 < r2: 
                    door_positions.append((r1, c1, 2)) 
                else:
                    door_positions.append((r2, c2, 2)) 
        
        return door_positions

    @staticmethod
    def build_grid_state(scenario):
        """Builds a grid where each cell is a dictionary with complete state"""
        rows, columns = scenario["grid_walls"].shape[:2]
        
        grid_state = np.empty((rows, columns), dtype=object)
        
        door_positions = ScenarioParser.compute_door_positions(scenario["doors"])
        
        for y in range(rows):
            for x in range(columns):
                walls = scenario["grid_walls"][y, x].tolist()
                
                fire = (y, x) in scenario["fires"]
                
                door = any((y, x, d) in door_positions for d in range(4))
                
                poi = None
                for p_y, p_x, p_type in scenario["pois"]:
                    if p_y == y and p_x == x:
                        poi = p_type
                        break
                
                cell = {
                    "walls": walls,
                    "fire": fire,
                    "smoke": False,
                    "damage": 0,
                    "door": door,
                    "poi": poi
                }
                
                grid_state[y, x] = cell
        
        return grid_state

class DirectionHelper:
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    
    DIRECTIONS = [
        (0, -1),  
        (1, 0),   
        (0, 1),   
        (-1, 0)   
    ]
    
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
            return None  
        
        if door_key in model.door_states:
            return model.door_states[door_key] 
        else:
            return "destroyed" 
    
    @staticmethod
    def is_entry(model, x, y):
        """Checks if a position is an entry point"""
        return (x, y) in [(e[1], e[0]) for e in model.scenario["entries"]]
    
    @staticmethod
    def damage_wall(model, y, x, direction):
        """Adds a damage point to a wall and checks if it gets destroyed"""
        wall_key = DirectionHelper.get_wall_key(y, x, direction)
        
        if wall_key not in model.wall_damage:
            model.wall_damage[wall_key] = 1
        else:
            model.wall_damage[wall_key] += 1
        
        model.damage_counters += 1
        
        if model.wall_damage[wall_key] >= 2:
            model.grid_state[y, x]["walls"][direction] = 0
            
            new_x, new_y = DirectionHelper.get_adjacent_position(x, y, direction)
            opposite_direction = DirectionHelper.get_opposite_direction(direction)
            
            if 0 <= new_y < model.grid.height and 0 <= new_x < model.grid.width:
                model.grid_state[new_y, new_x]["walls"][opposite_direction] = 0
                
            return True  
        
        return False  

class GameMechanics:
    @staticmethod
    def advance_fire(model):
        """Propagates fire through the scenario according to Flash Point: Fire Rescue rules"""
        rows, cols = model.grid_state.shape
        
        if not hasattr(model, 'victims_lost'):
            model.victims_lost = 0
        if not hasattr(model, 'damage_counters'):
            model.damage_counters = 0
        
        random_row = model.random.randint(1, rows-2)
        random_col = model.random.randint(1, cols-2)
        
        cell = model.grid_state[random_row, random_col]
        
        # Case 1: Cell with no fire or smoke -> Add SMOKE
        if not cell["fire"] and not cell["smoke"]:
            cell["smoke"] = True
        
        # Case 2: Cell with smoke -> Convert to fire
        elif not cell["fire"] and cell["smoke"]:
            cell["fire"] = True
            cell["smoke"] = False
            if (random_row, random_col) not in model.scenario["fires"]:
                model.scenario["fires"].append((random_row, random_col))
            
            # Check if there's a victim in the cell
            if cell["poi"] == "v":
                cell["poi"] = None
                model.victims_lost += 1
                
                # Update POIs in the scenario
                for i, poi in enumerate(model.scenario["pois"]):
                    if poi[0] == random_row and poi[1] == random_col:
                        model.scenario["pois"].pop(i)
                        break
        
        # Case 3: Cell with fire -> EXPLOSION
        elif cell["fire"]:
            for direction in range(4):
                GameMechanics.propagate_explosion(model, random_row, random_col, direction)
        
        # Smoke to fire propagation (second phase)
        new_fires = []
        new_smokes = []
        
        # Detect fire propagation
        for y in range(rows):
            for x in range(cols):
                if model.grid_state[y, x]["fire"]:
                    for direction in range(4):
                        if DirectionHelper.can_pass_wall(model, y, x, direction):
                            nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
                            
                            if 0 <= ny < rows and 0 <= nx < cols:
                                if not DirectionHelper.is_perimeter(model, nx, ny):
                                    if not model.grid_state[ny, nx]["fire"]:
                                        if model.grid_state[ny, nx]["smoke"]:
                                            new_fires.append((ny, nx))
                                        else:
                                            new_smokes.append((ny, nx))
        
        # Apply the detected changes - first apply the new fires
        for y, x in new_fires:
            model.grid_state[y, x]["fire"] = True
            model.grid_state[y, x]["smoke"] = False
            fire_pos = (y, x)
            if fire_pos not in model.scenario["fires"]:
                model.scenario["fires"].append(fire_pos)
            
            # Check if there's a victim in the cell
            if model.grid_state[y, x]["poi"] == "v":
                model.grid_state[y, x]["poi"] = None
                model.victims_lost += 1
                
                # Update POIs in the scenario
                for i, poi in enumerate(model.scenario["pois"]):
                    if poi[0] == y and poi[1] == x:
                        model.scenario["pois"].pop(i)
                        break
        
        # Apply new smokes
        for y, x in new_smokes:
            if (y, x) not in new_fires:  # Avoid duplicates
                model.grid_state[y, x]["smoke"] = True

    @staticmethod
    def propagate_explosion(model, row, col, direction):
        """Propagates an explosion in the specified direction until finding an obstacle"""
        rows, cols = model.grid_state.shape
        
        dx, dy = DirectionHelper.DIRECTIONS[direction]
        dir_name = DirectionHelper.DIRECTION_NAMES[direction]
        
        # Remove all doors adjacent to the original explosion point
        if direction == DirectionHelper.NORTH:
            door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
            
            for dir_check in range(4):
                door = (row, col, dir_check)
                if door in door_positions:
                    if door in model.door_states:
                        del model.door_states[door]
        
        # Start propagation
        x, y = col, row
        wall_found = False
        
        while not wall_found:
            # Calculate new position
            new_x, new_y = x + dx, y + dy
            
            # Check if within limits
            if new_y < 0 or new_y >= rows or new_x < 0 or new_x >= cols:
                break
                
            # Check if in perimeter
            if DirectionHelper.is_perimeter(model, new_x, new_y):
                break
            
            # Check for door in path
            door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
            door_in_path = (y, x, direction)
                
            if door_in_path in door_positions:
                if door_in_path in model.door_states:
                    del model.door_states[door_in_path]
                y = new_y
                x = new_x
                continue
            
            # Check for wall in path
            has_wall = DirectionHelper.has_wall(model, y, x, direction)
            wall_key = DirectionHelper.get_wall_key(y, x, direction)
            wall_destroyed = DirectionHelper.is_wall_destroyed(model, y, x, direction)
                
            if has_wall and not wall_destroyed:
                wall_destroyed = DirectionHelper.damage_wall(model, y, x, direction)
                
                if not wall_destroyed:
                    wall_found = True
                    break
            
            # If no wall or wall destroyed, continue propagation
            if not has_wall or wall_destroyed:
                x, y = new_x, new_y
                cell = model.grid_state[y, x]
                
                # Check for victim in cell
                if cell["poi"] == "v":
                    cell["poi"] = None
                    model.victims_lost += 1
                    
                    # Update POIs in the scenario
                    for i, poi in enumerate(model.scenario["pois"]):
                        if poi[0] == y and poi[1] == x:
                            model.scenario["pois"].pop(i)
                            break
                
                # Process fire/smoke effects
                if cell["smoke"]:
                    cell["smoke"] = False
                    cell["fire"] = True
                    if (y, x) not in model.scenario["fires"]:
                        model.scenario["fires"].append((y, x))
                
                elif not cell["fire"]:
                    cell["fire"] = True
                    if (y, x) not in model.scenario["fires"]:
                        model.scenario["fires"].append((y, x))
                
                else:
                    # If already fire, create shockwave
                    GameMechanics.shockwave(model, y, x, direction)
                    break

    @staticmethod
    def shockwave(model, row, col, direction):
        """
        Propagates a shockwave in the specified direction
        when an explosion reaches a cell that already has fire
        """
        rows, cols = model.grid_state.shape
        
        dx, dy = DirectionHelper.DIRECTIONS[direction]
        
        # Start propagation
        x, y = col, row
        stopped = False
        
        while not stopped:
            # Calculate new position
            new_x, new_y = x + dx, y + dy
            x, y = new_x, new_y
            
            # Check if within limits
            if y < 0 or y >= rows or x < 0 or x >= cols:
                break
            
            # Check for door in path
            door_key = (y-dy, x-dx, direction)
            door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
            
            if door_key in door_positions:
                if door_key in model.door_states:
                    door_state = model.door_states[door_key]
                    if door_state == "cerrada":  # "closed"
                        del model.door_states[door_key]
                else:
                    pass # Door already destroyed
            else:
                # Check for wall in path
                has_wall = DirectionHelper.has_wall(model, y-dy, x-dx, direction)
                
                if has_wall:
                    wall_destroyed = DirectionHelper.is_wall_destroyed(model, y-dy, x-dx, direction)
                    
                    if wall_destroyed:
                        pass # Continue through destroyed wall
                    else:
                        # Damage wall
                        wall_key = DirectionHelper.get_wall_key(y-dy, x-dx, direction)
                        DirectionHelper.damage_wall(model, y-dy, x-dx, direction)
                        
                        if wall_key in model.wall_damage:
                            damage = model.wall_damage[wall_key]
                        else:
                            damage = 1
                            
                        if damage < 2:
                            stopped = True
                            break
            
            # Check if in perimeter
            if DirectionHelper.is_perimeter(model, x, y):
                break
            
            # Process cell effects
            cell = model.grid_state[y, x]
            
            # Check for victim in cell
            if cell["poi"] == "v":
                cell["poi"] = None
                model.victims_lost += 1
                
                # Update POIs in scenario
                for i, poi in enumerate(model.scenario["pois"]):
                    if poi[0] == y and poi[1] == x:
                        model.scenario["pois"].pop(i)
                        break
            
            # Update cell state based on fire/smoke
            if cell["fire"]:
                # Continue through cells with fire
                pass
            elif cell["smoke"]:
                # Convert smoke to fire and stop
                cell["smoke"] = False
                cell["fire"] = True
                if (y, x) not in model.scenario["fires"]:
                    model.scenario["fires"].append((y, x))
                stopped = True
            else:
                # Place fire and stop
                cell["fire"] = True
                if (y, x) not in model.scenario["fires"]:
                    model.scenario["fires"].append((y, x))
                stopped = True

    @staticmethod
    def check_firefighters_in_fire(model):
        """Checks if there are firefighters in cells with fire and sends them to ambulance"""
        rows, cols = model.grid_state.shape
        injured_firefighters = []
        
        # Ambulance position
        ambulance_pos = (9, 0)
        
        # Find firefighters in cells with fire
        for y in range(rows):
            for x in range(cols):
                if model.grid_state[y, x]["fire"]:
                    cell_contents = model.grid.get_cell_list_contents((x, y))
                    firefighters = [agent for agent in cell_contents if isinstance(agent, FirefighterAgent)]
                    
                    for ff in firefighters:
                        injured_firefighters.append(ff)
        
        if not injured_firefighters:
            return
        
        # Process injured firefighters
        for ff in injured_firefighters:
            # If carrying victim, the victim is lost
            if ff.carrying:
                ff.carrying = False
                model.victims_lost += 1
                # Replenish POI when victim lost
                GameMechanics.replenish_pois(model)
            
            # Move to ambulance
            model.grid.remove_agent(ff)
            model.grid.place_agent(ff, ambulance_pos)
            
            # Reduce AP to 0
            ff.ap = 0

    @staticmethod
    def replenish_pois(model):
        """Replenishes POIs on the board to always maintain 3 POIs available"""
        current_pois_count = len(model.scenario["pois"])
        
        if current_pois_count >= 3:
            return
        
        pois_to_add = 3 - current_pois_count
        
        # Initialize POI deck if needed
        if not hasattr(model, "mazo_pois"):
            initial_victims_count = sum(1 for poi in model.scenario["pois"] if poi[2] == "v")
            initial_false_alarms_count = sum(1 for poi in model.scenario["pois"] if poi[2] == "f")
            
            remaining_victims = max(0, 10 - initial_victims_count)
            remaining_false_alarms = max(0, 5 - initial_false_alarms_count)
            
            model.mazo_pois = ["v"] * remaining_victims + ["f"] * remaining_false_alarms
            model.random.shuffle(model.mazo_pois)
        
        # Add new POIs
        for _ in range(pois_to_add):
            if not model.mazo_pois:
                break
            
            poi_type = model.mazo_pois.pop(0)
            
            # Find valid cell
            placed = False
            attempts = 0
            max_attempts = 100
            
            while not placed and attempts < max_attempts:
                attempts += 1
                
                # Generate random coordinates
                rows, cols = model.grid_state.shape
                row = model.random.randint(1, rows - 2)
                col = model.random.randint(1, cols - 2)
                
                # Check if valid cell
                if model.grid_state[row, col]["poi"] is None:
                    # Remove fire/smoke if present
                    if model.grid_state[row, col]["fire"]:
                        model.grid_state[row, col]["fire"] = False
                        if (row, col) in model.scenario["fires"]:
                            model.scenario["fires"].remove((row, col))
                    
                    if model.grid_state[row, col]["smoke"]:
                        model.grid_state[row, col]["smoke"] = False
                    
                    # Place POI
                    model.grid_state[row, col]["poi"] = poi_type
                    model.scenario["pois"].append((row, col, poi_type))
                    
                    # Check if firefighter already present
                    cell_contents = model.grid.get_cell_list_contents((col, row))
                    firefighters = [agent for agent in cell_contents if isinstance(agent, FirefighterAgent)]
                    
                    if firefighters:
                        if poi_type == "f":  # False alarm
                            model.grid_state[row, col]["poi"] = None
                            model.scenario["pois"].remove((row, col, poi_type))
                    
                    placed = True
            
            if not placed:
                # Return card to deck and shuffle
                model.mazo_pois.append(poi_type)
                model.random.shuffle(model.mazo_pois)

    @staticmethod
    def check_end_conditions(model):
        """
        Checks if victory or defeat conditions have been met
        
        Returns:
            bool: True if game has ended, False if it continues
        """
        # Victory condition: 7+ rescued victims
        if model.victims_rescued >= 7:
            model.simulation_over = True
            return True
            
        # Defeat by lost victims: 4+ victims
        elif model.victims_lost >= 4:
            model.simulation_over = True
            return True
            
        # Defeat by structural collapse: 24+ damage
        elif model.damage_counters >= 24:
            model.simulation_over = True
            return True
            
        # Game continues
        return False

class FirefighterAgent(Agent):
    """Firefighter agent that rescues victims from the fire"""
    
    def __init__(self, unique_id, model, pos):
        super().__init__(model)
        self.unique_id = unique_id
        self.ap = 4  # Action points
        self.carrying = False  # If carrying a victim
        self.assigned_entry = None
        self.direction = None
        self.max_ap = 8
    
    def extinguish_fire(self, cell_y, cell_x, type="fire"):
        """Attempts to extinguish fire or smoke in a specific cell"""
        cell = self.model.grid_state[cell_y, cell_x]
        
        if type == "fire" and cell["fire"]:
            if self.ap >= 2:
                cell["fire"] = False
                if (cell_y, cell_x) in self.model.scenario["fires"]:
                    self.model.scenario["fires"].remove((cell_y, cell_x))
                ap_before = self.ap
                self.ap -= 2

                grid_changes = [{"x": cell_x, "y": cell_y, "fire": False, "smoke": False}]
                
                self.model.json_exporter.action_frame(
                    self.model,
                    self.unique_id,
                    "extinguish_fire",
                    ap_before=ap_before,
                    ap_after=self.ap,
                    target=[cell_x, cell_y],
                    grid_changes=grid_changes
                )
                return True
        
        elif type == "convert" and cell["fire"]:
            if self.ap >= 1:
                ap_before = self.ap
                cell["fire"] = False
                cell["smoke"] = True
                if (cell_y, cell_x) in self.model.scenario["fires"]:
                    self.model.scenario["fires"].remove((cell_y, cell_x))
                self.ap -= 1
                
                grid_changes = [{"x": cell_x, "y": cell_y, "fire": False, "smoke": True}]
                
                self.model.json_exporter.action_frame(
                    self.model,
                    self.unique_id,
                    "convert_to_smoke",
                    ap_before=ap_before,
                    ap_after=self.ap,
                    target=[cell_x, cell_y],
                    grid_changes=grid_changes
                )
                return True
        
        elif type == "smoke" and cell["smoke"]:
            if self.ap >= 1:
                ap_before = self.ap
                cell["smoke"] = False
                self.ap -= 1
                
                grid_changes = [{"x": cell_x, "y": cell_y, "smoke": False}]
                
                self.model.json_exporter.action_frame(
                    self.model,
                    self.unique_id,
                    "remove_smoke",
                    ap_before=ap_before,
                    ap_after=self.ap,
                    target=[cell_x, cell_y],
                    grid_changes=grid_changes
                )
                return True
            return False
        
        return False
    
    def open_close_door(self, direction):
        """Opens or closes an adjacent door in the specified direction"""
        if self.ap < 1:
            return False
        
        x, y = self.pos
        
        if DirectionHelper.is_door(self.model, y, x, direction):
            door_pos = DirectionHelper.get_wall_key(y, x, direction)
            
            if door_pos not in self.model.door_states:
                self.model.door_states[door_pos] = "closed"
            
            new_state = "open" if self.model.door_states[door_pos] == "closed" else "closed"
            self.model.door_states[door_pos] = new_state
            
            self.ap -= 1
            return True
        else:
            return False
    
    def cut_wall(self, direction):
        """Cuts an adjacent wall in the specified direction"""
        if self.ap < 2:
            return False
        
        x, y = self.pos
        
        if DirectionHelper.has_wall(self.model, y, x, direction):
            nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
            
            is_perimeter = DirectionHelper.is_perimeter(self.model, nx, ny)
            
            if is_perimeter:
                return False
            
            wall_destroyed = DirectionHelper.damage_wall(self.model, y, x, direction)
            self.ap -= 2
            return True
        else:
            return False
    
    def step(self):
        # If we are in the board entry phase
        if self.model.stage == 1 and self.assigned_entry is not None:
            self.model.grid.move_agent(self, self.assigned_entry)
            self.assigned_entry = None
            return
        
        # While there are action points, allow actions
        while self.ap > 0:
            x, y = self.pos
            current_cell = self.model.grid_state[y, x]
            
            # Check for POI in current cell
            if current_cell["poi"] is not None:
                if current_cell["poi"] == "v" and not self.carrying:
                    self.carrying = True
                    current_cell["poi"] = None
                elif current_cell["poi"] == "f":
                    current_cell["poi"] = None
            
            # Check for rescue at entry with victim
            if self.carrying:
                is_entry = self.pos in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                is_perimeter = self.pos[0] == 0 or self.pos[0] == self.model.grid.width - 1 or \
                            self.pos[1] == 0 or self.pos[1] == self.model.grid.height - 1
                
                if is_entry and is_perimeter:
                    self.carrying = False
                    return
        
            # Generate possible actions
            possible_actions = []
            possible_actions.append("move")
            
            # Get adjacent cells
            adjacent_cells = []
            for direction in range(4):
                nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
                if 0 <= ny < self.model.grid.height and 0 <= nx < self.model.grid.width:
                    if DirectionHelper.can_pass_wall(self.model, y, x, direction):
                        adjacent_cells.append((ny, nx))

            # Check for fire actions
            if current_cell["fire"] and self.ap >= 2:
                possible_actions.append("extinguish_fire")
                possible_actions.append("convert_fire_to_smoke")
            
            if current_cell["smoke"] and self.ap >= 1:
                possible_actions.append("remove_smoke")
            
            for cell_y, cell_x in adjacent_cells:
                if self.model.grid_state[cell_y, cell_x]["fire"] and self.ap >= 2:
                    possible_actions.append("extinguish_adjacent_fire")
                    possible_actions.append("convert_adjacent_fire_to_smoke")
                if self.model.grid_state[cell_y, cell_x]["smoke"] and self.ap >= 1:
                    possible_actions.append("remove_adjacent_smoke")
            
            # Check for door actions
            walls = current_cell["walls"]
            for i in range(4):
                door_pos = None
                if i == 0 and y > 0:
                    door_pos = (y, x, 0)
                elif i == 1 and x < self.model.grid.width - 1:
                    door_pos = (y, x, 1)
                elif i == 2 and y < self.model.grid.height - 1:
                    door_pos = (y, x, 2)
                elif i == 3 and x > 0:
                    door_pos = (y, x, 3)
                
                if door_pos:
                    door_positions = ScenarioParser.compute_door_positions(self.model.scenario["doors"])
                    if door_pos in door_positions and self.ap >= 1:
                        possible_actions.append(f"door_{i}")
            
            # Check for wall cutting actions
            for i in range(4):
                if walls[i] == 1 and self.ap >= 2:
                    is_perimeter = False
                    
                    if i == 0 and y == 1:
                        is_perimeter = True
                    elif i == 1 and x == self.model.grid.width - 2:
                        is_perimeter = True
                    elif i == 2 and y == self.model.grid.height - 2:
                        is_perimeter = True
                    elif i == 3 and x == 1:
                        is_perimeter = True
                            
                    if (y == 0 and i == 0) or \
                    (x == self.model.grid.width - 1 and i == 1) or \
                    (y == self.model.grid.height - 1 and i == 2) or \
                    (x == 0 and i == 3):
                        is_perimeter = True
                        
                    if not is_perimeter:
                        possible_actions.append(f"cut_{i}")
            
            # Consider passing turn
            is_ambulance = (x == 9 and y == 0)
            
            if (len(possible_actions) == 0) or (self.ap <= 4) or is_ambulance:
                possible_actions.append("pass")
                
            # Choose action randomly
            action = self.model.random.choice(possible_actions)
            
            # Execute chosen action
            if action == "move":
                self._perform_movement()
            elif action == "extinguish_fire":
                self.extinguish_fire(y, x, "fire")
            elif action == "convert_fire_to_smoke":
                self.extinguish_fire(y, x, "convert")
            elif action == "remove_smoke":
                self.extinguish_fire(y, x, "smoke")
            elif action == "extinguish_adjacent_fire":
                cells_with_fire = [(cy, cx) for cy, cx in adjacent_cells 
                                 if self.model.grid_state[cy, cx]["fire"]]
                if cells_with_fire:
                    cy, cx = self.model.random.choice(cells_with_fire)
                    self.extinguish_fire(cy, cx, "fire")
            elif action == "convert_adjacent_fire_to_smoke":
                cells_with_fire = [(cy, cx) for cy, cx in adjacent_cells 
                                 if self.model.grid_state[cy, cx]["fire"]]
                if cells_with_fire:
                    cy, cx = self.model.random.choice(cells_with_fire)
                    self.extinguish_fire(cy, cx, "convert")
            elif action == "remove_adjacent_smoke":
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
                break
    
    def _perform_movement(self):
        """Helper method to perform a movement, respecting constraints"""
        x, y = self.pos
        original_pos = [x, y]
        ap_before = self.ap
        
        movements = []
        
        for direction in range(4):
            if DirectionHelper.can_pass_wall(self.model, y, x, direction):
                nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
                
                if 0 <= ny < self.model.grid.height and 0 <= nx < self.model.grid.width:
                    dest_cell = self.model.grid_state[ny, nx]
                    is_perimeter = DirectionHelper.is_perimeter(self.model, nx, ny)
                    is_entry = DirectionHelper.is_entry(self.model, nx, ny)
                    
                    ap_cost = 1
                    
                    if dest_cell["fire"]:
                        ap_cost = 2
                    
                    if self.carrying:
                        ap_cost = 2
                    
                    can_go = True
                    if self.carrying and dest_cell["fire"]:
                        can_go = False
                    
                    if self.ap < ap_cost:
                        can_go = False
                    
                    if can_go and (not is_perimeter or (self.carrying and is_entry)):
                        movements.append((nx, ny, ap_cost))
        
        if not movements:
            return False
        
        new_pos_info = self.model.random.choice(movements)
        new_pos = (new_pos_info[0], new_pos_info[1])
        ap_cost = new_pos_info[2]
        
        is_entry = new_pos in [(e[1], e[0]) for e in self.model.scenario["entries"]]
        is_perimeter = new_pos[0] == 0 or new_pos[0] == self.model.grid.width - 1 or \
                     new_pos[1] == 0 or new_pos[1] == self.model.grid.height - 1
        
        self.model.grid.move_agent(self, new_pos)
        self.ap -= ap_cost

        self.model.json_exporter.action_frame(
            self.model,
            self.unique_id,
            "move",
            ap_before=ap_before, 
            ap_after=self.ap,
            from_pos=original_pos,
            to=[new_pos[0], new_pos[1]]
        )
        
        if self.carrying and is_entry and is_perimeter:
            self.carrying = False
            self.model.victims_rescued += 1
            GameMechanics.replenish_pois(self.model)
            return True
        else:
            new_x, new_y = new_pos
            new_cell = self.model.grid_state[new_y, new_x]
            
            if new_cell["poi"] is not None:
                poi_type = new_cell["poi"]
                
                if poi_type == "v" and not self.carrying:
                    self.carrying = True
                    new_cell["poi"] = None
                    
                    for i, poi in enumerate(self.model.scenario["pois"]):
                        if poi[0] == new_y and poi[1] == new_x:
                            self.model.scenario["pois"].pop(i)
                            break
                
                elif poi_type == "f":
                    new_cell["poi"] = None
                    
                    for i, poi in enumerate(self.model.scenario["pois"]):
                        if poi[0] == new_y and poi[1] == new_x:
                            self.model.scenario["pois"].pop(i)
                            break
                    
                    GameMechanics.replenish_pois(self.model)
            
            return True
        
class FireRescueModel(Model):
    """Fire rescue simulation model"""
    
    def __init__(self, scenario):
        super().__init__()
        
        self.grid = MultiGrid(10, 8, False)
        self.schedule = RandomActivation(self)
        self.scenario = scenario
        self.grid_state = ScenarioParser.build_grid_state(scenario)
        self.door_states = {}
        
        door_positions = ScenarioParser.compute_door_positions(scenario["doors"])
        for door_pos in door_positions:
            self.door_states[door_pos] = "closed"
        
        self.wall_damage = {}
        self.victims_lost = 0
        self.victims_rescued = 0
        self.damage_counters = 0
        self.simulation_over = False
        
        self.create_agents()
        self.step_count = 0
        self.stage = 0
        self.mazo_pois = []
        self.json_exporter = JSONExporter()
    
    def create_agents(self):
        """Create 6 firefighter agents distributed among available entries"""
        num_firefighters = 6
        num_entries = len(self.scenario["entries"])
        
        for i in range(num_firefighters):
            entry_idx = i % num_entries
            pos = self.scenario["entries"][entry_idx]
            row, column = pos
            
            rows, columns = self.grid_state.shape
            north_dist = row
            south_dist = rows - 1 - row
            west_dist = column
            east_dist = columns - 1 - column
            
            if north_dist <= min(south_dist, west_dist, east_dist):
                ext_row, ext_col = row - 1, column
                direction = "north"
            elif south_dist <= min(north_dist, west_dist, east_dist):
                ext_row, ext_col = row + 1, column
                direction = "south"
            elif west_dist <= min(north_dist, south_dist, east_dist):
                ext_row, ext_col = row, column - 1
                direction = "west"
            else:
                ext_row, ext_col = row, column + 1
                direction = "east"
            
            mesa_ext_pos = (ext_col, ext_row)
            agent = FirefighterAgent(i, self, mesa_ext_pos)
            agent.assigned_entry = (column, row)
            agent.direction = direction
            
            try:
                self.grid.place_agent(agent, mesa_ext_pos)
            except Exception as e:
                self.grid.place_agent(agent, (column, row))
                
            self.schedule.add(agent)
    
    def step(self):
        """Advance simulation one step"""
        if self.simulation_over:
            return
                    
        if self.step_count == 0:
            self.json_exporter.initial_state(self)
                    
        self.step_count += 1

        if self.stage == 0:
            self.stage = 1
        
        grid_before = self._copy_grid_state()
        self.schedule.step()

        if self.step_count > 1:
            GameMechanics.advance_fire(self)
            GameMechanics.check_firefighters_in_fire(self)

        grid_changes = self._calculate_grid_changes(grid_before)
        GameMechanics.replenish_pois(self)

        for agent in self.schedule.agents:
            agent.ap = min(agent.ap + 4, agent.max_ap)

        game_over_result = GameMechanics.check_end_conditions(self)

        if self.simulation_over:
            result = ""
            message = ""
            
            if self.victims_rescued >= 7:
                result = "victory"
                message = f"All {self.victims_rescued} victims rescued! Congratulations!"
            elif self.victims_lost >= 4:
                result = "defeat_victims"
                message = f"{self.victims_lost} victims were lost in the fire."
            else:
                result = "defeat_collapse"
                message = f"Building collapsed with {self.damage_counters} damage points."
                
            self.json_exporter.game_over(self, result, message)
        else:
            self.json_exporter.end_of_turn(self, grid_changes)

    def _copy_grid_state(self):
        """Creates a copy of the grid state to compare changes"""
        import copy
        return copy.deepcopy(self.grid_state)
    
    def _calculate_grid_changes(self, grid_before):
        """Calculates changes in the grid between two states"""
        grid_changes = []
        
        for y in range(self.grid_state.shape[0]):
            for x in range(self.grid_state.shape[1]):
                before = grid_before[y, x]
                after = self.grid_state[y, x]
                
                if (before["fire"] != after["fire"] or
                    before["smoke"] != after["smoke"] or
                    before["poi"] != after["poi"]):
                    
                    change = {
                        "x": x,
                        "y": y
                    }
                    
                    if before["fire"] != after["fire"]:
                        change["fire"] = after["fire"]
                    
                    if before["smoke"] != after["smoke"]:
                        change["smoke"] = after["smoke"]
                    
                    if before["poi"] != after["poi"]:
                        change["poi"] = after["poi"]
                    
                    grid_changes.append(change)
        
        return grid_changes
    
class Visualization:
    """Class that encapsulates all visualization functionalities"""
    
    @staticmethod
    def visualize_grid_with_perimeter_and_doors(grid, door_positions, entries, fires=None, pois=None, model=None):
        """Visualizes the game board with all its elements"""
        rows, columns = grid.shape[:2]
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_facecolor('#d9f2d9')

        # Determine entry directions
        entry_positions = []
        for y, x in entries:
            north_dist = y
            south_dist = rows - 1 - y
            west_dist = x
            east_dist = columns - 1 - x
            
            min_dist = min(north_dist, south_dist, west_dist, east_dist)
            
            if min_dist == north_dist:
                entry_positions.append((y, x, 0))  # North
            elif min_dist == east_dist:
                entry_positions.append((y, x, 1))  # East
            elif min_dist == south_dist:
                entry_positions.append((y, x, 2))  # South
            else:
                entry_positions.append((y, x, 3))  # West

        for y in range(rows):
            for x in range(columns):
                # Check cell state
                is_fire = (y, x) in fires if fires else False
                is_smoke = False
                
                if model is not None:
                    is_smoke = model.grid_state[y, x]["smoke"]
                
                # Set background color
                if is_fire:
                    color = '#ffcccc'  # Fire
                elif is_smoke:
                    color = '#e6e6e6'  # Smoke
                elif x == 0 or x == columns-1 or y == 0 or y == rows-1:
                    color = '#b3e6b3'  # Perimeter
                else:
                    color = '#e6f7ff'  # Playable cells
                    
                rect = patches.Rectangle((x, rows - y - 1), 1, 1, linewidth=0, facecolor=color)
                ax.add_patch(rect)

                # Draw grid lines
                ax.plot([x, x+1], [rows - y - 1, rows - y - 1], color='gray', linewidth=0.3)
                ax.plot([x, x+1], [rows - y, rows - y], color='gray', linewidth=0.3)
                ax.plot([x, x], [rows - y - 1, rows - y], color='gray', linewidth=0.3)
                ax.plot([x+1, x+1], [rows - y - 1, rows - y], color='gray', linewidth=0.3)

                # Draw fire symbol
                if is_fire:
                    ax.plot(x + 0.5, rows - y - 0.5, 'o', markersize=15, 
                            markerfacecolor='#ff6600', markeredgecolor='red', alpha=0.7)
                    ax.plot(x + 0.5, rows - y - 0.5, '*', markersize=10, 
                            markerfacecolor='yellow', markeredgecolor='yellow')
                
                # Draw smoke symbol
                elif is_smoke:
                    ax.plot(x + 0.5, rows - y - 0.5, 's', markersize=14, 
                            markerfacecolor='#a6a6a6', markeredgecolor='#808080', alpha=0.6)
                    ax.plot(x + 0.5, rows - y - 0.5, 'o', markersize=8, 
                            markerfacecolor='#d3d3d3', markeredgecolor='#d3d3d3', alpha=0.8)

                # Draw POIs
                if pois:
                    for poi_y, poi_x, poi_type in pois:
                        if poi_y == y and poi_x == x:
                            if poi_type == 'v':  # Victim
                                ax.plot(x + 0.5, rows - y - 0.5, 'D', markersize=12, 
                                        markerfacecolor='#00cc66', markeredgecolor='black', zorder=10)
                            elif poi_type == 'f':  # False alarm
                                ax.plot(x + 0.5, rows - y - 0.5, 'X', markersize=12, 
                                        markerfacecolor='#cccccc', markeredgecolor='black', zorder=10)
                                
                # Handle perimeter walls
                is_perimeter = (x == 0 or x == columns-1 or y == 0 or y == rows-1)
                if is_perimeter:
                    if y == 0:
                        ax.plot([x, x+1], [rows - y, rows - y], color='black', linewidth=2.5)
                    if y == rows-1:
                        ax.plot([x, x+1], [rows - y - 1, rows - y - 1], color='black', linewidth=2.5)
                    if x == 0:
                        ax.plot([x, x], [rows - y - 1, rows - y], color='black', linewidth=2.5)
                    if x == columns-1:
                        ax.plot([x+1, x+1], [rows - y - 1, rows - y], color='black', linewidth=2.5)
                else:
                    # Get wall data
                    if model is not None:
                        wall_n, wall_e, wall_s, wall_w = model.grid_state[y, x]["walls"]
                    else:
                        wall_n, wall_e, wall_s, wall_w = grid[y, x]

                    # Check for doors and entries
                    door_n = (y, x, 0) in door_positions
                    door_e = (y, x, 1) in door_positions
                    door_s = (y, x, 2) in door_positions
                    door_w = (y, x, 3) in door_positions
                    
                    entry_n = (y, x, 0) in entry_positions
                    entry_e = (y, x, 1) in entry_positions
                    entry_s = (y, x, 2) in entry_positions
                    entry_w = (y, x, 3) in entry_positions

                    # North direction
                    if entry_n:
                        ax.plot([x+0.25, x+0.75], [rows - y, rows - y], color='white', linewidth=4.0)
                    elif door_n:
                        door_color = 'brown'
                        if model is not None and (y, x, 0) in model.door_states:
                            door_open = model.door_states[(y, x, 0)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        elif model is not None:
                            door_color = 'lightgreen'  # Destroyed doors
                        ax.plot([x+0.25, x+0.75], [rows - y, rows - y], color=door_color, linewidth=2.5)
                    elif wall_n:
                        wall_color = 'black'
                        if model is not None and (y, x, 0) in model.wall_damage:
                            if model.wall_damage[(y, x, 0)] == 1:
                                wall_color = 'orange'  # Damaged once
                            elif model.wall_damage[(y, x, 0)] >= 2:
                                wall_color = None  # Destroyed
                        
                        if wall_color:
                            ax.plot([x, x+1], [rows - y, rows - y], color=wall_color, linewidth=2.5)
                    
                    # East direction
                    if entry_e:
                        ax.plot([x+1, x+1], [rows - y - 0.75, rows - y - 0.25], color='white', linewidth=4.0)
                    elif door_e:
                        door_color = 'brown'
                        if model is not None and (y, x, 1) in model.door_states:
                            door_open = model.door_states[(y, x, 1)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        elif model is not None:
                            door_color = 'lightgreen'
                        ax.plot([x+1, x+1], [rows - y - 0.75, rows - y - 0.25], color=door_color, linewidth=2.5)
                    elif wall_e:
                        wall_color = 'black'
                        if model is not None and (y, x, 1) in model.wall_damage:
                            if model.wall_damage[(y, x, 1)] == 1:
                                wall_color = 'orange'
                            elif model.wall_damage[(y, x, 1)] >= 2:
                                wall_color = None
                        
                        if wall_color:
                            ax.plot([x+1, x+1], [rows - y - 1, rows - y], color=wall_color, linewidth=2.5)
                    
                    # South direction
                    if entry_s:
                        ax.plot([x+0.25, x+0.75], [rows - y - 1, rows - y - 1], color='white', linewidth=4.0)
                    elif door_s:
                        door_color = 'brown'
                        if model is not None and (y, x, 2) in model.door_states:
                            door_open = model.door_states[(y, x, 2)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        elif model is not None:
                            door_color = 'lightgreen'
                        ax.plot([x+0.25, x+0.75], [rows - y - 1, rows - y - 1], color=door_color, linewidth=2.5)
                    elif wall_s:
                        wall_color = 'black'
                        if model is not None and (y, x, 2) in model.wall_damage:
                            if model.wall_damage[(y, x, 2)] == 1:
                                wall_color = 'orange'
                            elif model.wall_damage[(y, x, 2)] >= 2:
                                wall_color = None
                        
                        if wall_color:
                            ax.plot([x, x+1], [rows - y - 1, rows - y - 1], color=wall_color, linewidth=2.5)
                    
                    # West direction
                    if entry_w:
                        ax.plot([x, x], [rows - y - 0.75, rows - y - 0.25], color='white', linewidth=4.0)
                    elif door_w:
                        door_color = 'brown'
                        if model is not None and (y, x, 3) in model.door_states:
                            door_open = model.door_states[(y, x, 3)] == "open"
                            door_color = 'green' if door_open else 'brown'
                        elif model is not None:
                            door_color = 'lightgreen'
                        ax.plot([x, x], [rows - y - 0.75, rows - y - 0.25], color=door_color, linewidth=2.5)
                    elif wall_w:
                        wall_color = 'black'
                        if model is not None and (y, x, 3) in model.wall_damage:
                            if model.wall_damage[(y, x, 3)] == 1:
                                wall_color = 'orange'
                            elif model.wall_damage[(y, x, 3)] >= 2:
                                wall_color = None
                        
                        if wall_color:
                            ax.plot([x, x], [rows - y - 1, rows - y], color=wall_color, linewidth=2.5)
                        
        # Create legend elements
        entry_line = plt.Line2D([0], [0], color='white', linewidth=4.0, label='Firefighter entry')
        perimeter_patch = patches.Patch(color='#b3e6b3', label='Perimeter')
        playable_patch = patches.Patch(color='#e6f7ff', label='Playable cell')
        door_line = plt.Line2D([0], [0], color='brown', linewidth=2.5, label='Door')
        wall_line = plt.Line2D([0], [0], color='black', linewidth=2.5, label='Wall')
        fire_marker = plt.Line2D([0], [0], marker='o', markersize=15, markerfacecolor='#ff6600', 
                                markeredgecolor='red', alpha=0.7, linestyle='', label='Fire')
        smoke_marker = plt.Line2D([0], [0], marker='s', markersize=14, markerfacecolor='#a6a6a6', 
                                markeredgecolor='#808080', alpha=0.6, linestyle='', label='Smoke')
        victim_marker = plt.Line2D([0], [0], marker='D', markersize=12, markerfacecolor='#00cc66', 
                                markeredgecolor='black', linestyle='', label='Victim (POI)')
        false_alarm_marker = plt.Line2D([0], [0], marker='X', markersize=12, markerfacecolor='#cccccc', 
                                markeredgecolor='black', linestyle='', label='False alarm (POI)')

        if model is not None:
            # Add firefighters to the grid and legend
            firefighter_marker = plt.Line2D([0], [0], marker='o', markersize=15, 
                                      markerfacecolor='blue', markeredgecolor='navy', 
                                      alpha=0.7, linestyle='', label='Firefighter')
            
            ax.legend(handles=[perimeter_patch, playable_patch, entry_line, wall_line, 
                              door_line, fire_marker, victim_marker, false_alarm_marker,
                              firefighter_marker], 
                      loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
            
            ax.set_xlim(-1, columns+1) 
            ax.set_ylim(-1, rows+1)
            
            # Draw firefighters
            for agent in model.schedule.agents:
                x, y = agent.pos
                ax.plot(x + 0.5, rows - y - 0.5, 'o', markersize=24, 
                        markerfacecolor='blue', markeredgecolor='navy', alpha=0.7, zorder=25)
                ax.text(x + 0.5, rows - y - 0.5, str(agent.unique_id), color='white', 
                        fontsize=12, ha='center', va='center', zorder=26)
            
            ax.set_title(f"Simulation - Step {model.step_count}")
        else:
            ax.legend(handles=[perimeter_patch, playable_patch, entry_line, wall_line, door_line, 
                            fire_marker, smoke_marker, victim_marker, false_alarm_marker], 
                    loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
            ax.set_title("6×8 Scenario Map with Perimeter (8×10), Walls and Doors")
            
        # Final formatting
        ax.set_xticks(range(columns))
        ax.set_yticks(range(rows))
        ax.set_xticklabels(range(columns))
        ax.set_yticklabels(range(rows - 1, -1, -1))
        ax.set_aspect('equal')
        ax.grid(False)
        plt.tight_layout()
        return fig, ax

    @staticmethod
    def visualize_simulation(model):
        """Visualizes the current state of the simulation, including firefighters"""
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
while not model.simulation_over and step < 50:
    print(f"\n--- Paso {step} ---")
    model.step()
    Visualization.visualize_simulation(model)  # Usa la función existente
    step += 1

print("\n=== SIMULATION FINISHED ===")
print(f"Total steps executed: {step-1}")
print(f"Victims rescued: {model.victims_rescued}")
print(f"Victims lost: {model.victims_lost}")
print(f"Accumulated wall damage: {model.damage_counters}")