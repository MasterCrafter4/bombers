from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid  
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
import os
import heapq
import csv
import time
from datetime import datetime
import signal
from contextlib import contextmanager
import signal

# class JSONExporter:
#     """Class to export game state to JSON files for Unity"""
    
#     def __init__(self, output_dir="game_data"):
#         self.frame_counter = 0
#         self.output_dir = output_dir
        
#         if not os.path.exists(output_dir):
#             os.makedirs(output_dir)
    
#     def save_frame(self, data):
#         """Saves a frame as a JSON file"""
#         filename = os.path.join(self.output_dir, f"frame_{self.frame_counter:04d}.json")
#         with open(filename, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=2)
#         self.frame_counter += 1
#         return data
    
#     def initial_state(self, model):
#         """Generates the JSON for the initial game state"""
#         firefighters = []
#         for agent in model.schedule.agents:
#             x, y = agent.pos
#             firefighters.append({
#                 "id": agent.unique_id,
#                 "x": x,
#                 "y": y,
#                 "ap": agent.ap,
#                 "carrying": agent.carrying
#             })
        
#         cells = []
#         for y in range(model.grid.height):
#             for x in range(model.grid.width):
#                 if x < model.grid_state.shape[1] and y < model.grid_state.shape[0]:
#                     cell = model.grid_state[y, x]
#                     cell_json = {
#                         "x": x,
#                         "y": y,
#                         "walls": [bool(wall) for wall in cell["walls"]],
#                         "door": cell["door"],
#                         "fire": cell["fire"],
#                         "smoke": cell["smoke"],
#                         "poi": cell["poi"]
#                     }
#                     cells.append(cell_json)
        
#         doors = []
#         door_positions = ScenarioParser.compute_door_positions(model.scenario["doors"])
#         for (r1, c1), (r2, c2) in model.scenario["doors"]:
#             door_state = "closed"
#             for pos in door_positions:
#                 if pos in model.door_states:
#                     door_state = model.door_states[pos]
            
#             doors.append({
#                 "from": [c1, r1],
#                 "to": [c2, r2],
#                 "state": door_state
#             })
        
#         pois = []
#         for y, x, poi_type in model.scenario["pois"]:
#             pois.append({
#                 "x": x,
#                 "y": y,
#                 "type": poi_type
#             })
        
#         entries = [[x, y] for y, x in model.scenario["entries"]]
        
#         data = {
#             "frame": 0,
#             "turn": 0,
#             "action": {
#                 "type": "initial_state"
#             },
#             "firefighters": firefighters,
#             "grid": {
#                 "width": model.grid.width,
#                 "height": model.grid.height,
#                 "cells": cells
#             },
#             "doors": doors,
#             "pois": pois,
#             "entries": entries,
#             "wall_damage": [],
#             "summary": {
#                 "rescued": 0,
#                 "lost": 0,
#                 "damage": 0,
#                 "pois_in_deck": len(model.mazo_pois) if hasattr(model, "mazo_pois") else 15
#             }
#         }
        
#         return self.save_frame(data)
    
#     def action_frame(self, model, firefighter_id, action_type, **kwargs):
#         """Generates the JSON for an individual action"""
#         agent = None
#         for a in model.schedule.agents:
#             if a.unique_id == firefighter_id:
#                 agent = a
#                 break
        
#         if not agent:
#             return None
        
#         x, y = agent.pos
        
#         data = {
#             "frame": self.frame_counter,
#             "turn": model.step_count,
#             "action": {
#                 "firefighter_id": firefighter_id,
#                 "type": action_type,
#                 "ap_before": kwargs.get("ap_before", 0),
#                 "ap_after": kwargs.get("ap_after", 0)
#             },
#             "firefighters": [
#                 {
#                     "id": firefighter_id,
#                     "x": x,
#                     "y": y,
#                     "ap": agent.ap,
#                     "carrying": agent.carrying
#                 }
#             ],
#             "grid_changes": kwargs.get("grid_changes", []),
#             "wall_damage": kwargs.get("wall_damage", []),
#             "doors": kwargs.get("doors", []),
#             "pois": kwargs.get("pois", [])
#         }
        
#         if action_type == "move":
#             data["action"]["from"] = kwargs.get("from_pos", [0, 0])
#             data["action"]["to"] = kwargs.get("to", [x, y])
#         elif action_type in ["extinguish_fire", "convert_to_smoke", "remove_smoke"]:
#             data["action"]["target"] = kwargs.get("target", [0, 0])
#         elif action_type == "pickup_poi":
#             data["action"]["target"] = kwargs.get("target", [0, 0])
#             data["action"]["poi_type"] = kwargs.get("poi_type", "")
        
#         return self.save_frame(data)
    
#     def end_of_turn(self, model, grid_changes=None):
#         """Generates the JSON for the end of turn"""
#         firefighters = []
#         for agent in model.schedule.agents:
#             x, y = agent.pos
#             firefighters.append({
#                 "id": agent.unique_id,
#                 "x": x,
#                 "y": y,
#                 "ap": agent.ap,
#                 "carrying": agent.carrying
#             })
        
#         if grid_changes is None:
#             grid_changes = []
        
#         pois = []
#         for y, x, poi_type in model.scenario["pois"]:
#             pois.append({
#                 "x": x,
#                 "y": y,
#                 "type": poi_type
#             })
        
#         data = {
#             "frame": self.frame_counter,
#             "turn": model.step_count,
#             "action": {
#                 "type": "end_of_turn"
#             },
#             "firefighters": firefighters,
#             "grid_changes": grid_changes,
#             "wall_damage": [],
#             "doors": [],
#             "pois": pois,
#             "summary": {
#                 "rescued": model.victims_rescued,
#                 "lost": model.victims_lost,
#                 "damage": model.damage_counters,
#                 "pois_in_deck": len(model.mazo_pois) if hasattr(model, "mazo_pois") else 0
#             }
#         }
        
#         return self.save_frame(data)
    
#     def game_over(self, model, result, message):
#         """Generates the JSON for game over"""
#         data = {
#             "frame": self.frame_counter,
#             "turn": model.step_count,
#             "action": {
#                 "type": "game_over",
#                 "result": result,
#                 "message": message
#             },
#             "summary": {
#                 "rescued": model.victims_rescued,
#                 "lost": model.victims_lost,
#                 "damage": model.damage_counters
#             }
#         }
        
#         return self.save_frame(data)

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
        
        # Initialize POI deck if needed or if it's empty
        if not hasattr(model, "mazo_pois") or len(model.mazo_pois) == 0:
            initial_victims_count = sum(1 for poi in model.scenario["pois"] if poi[2] == "v")
            initial_false_alarms_count = sum(1 for poi in model.scenario["pois"] if poi[2] == "f")
            
            remaining_victims = max(0, 10 - initial_victims_count)
            remaining_false_alarms = max(0, 5 - initial_false_alarms_count)
            
            model.mazo_pois = ["v"] * remaining_victims + ["f"] * remaining_false_alarms
            model.random.shuffle(model.mazo_pois)
        
        # Add new POIs
        pois_added = 0
        for _ in range(pois_to_add):
            if not model.mazo_pois:
                break
            
            poi_type = model.mazo_pois.pop(0)
            
            # Get all valid cells first
            valid_cells = []
            rows, cols = model.grid_state.shape
            
            for row in range(1, rows-1):
                for col in range(1, cols-1):
                    # Skip cells that already have POIs
                    if model.grid_state[row, col]["poi"] is not None:
                        continue
                        
                    # Skip cells with walls on all sides (unreachable)
                    has_access = False
                    for direction in range(4):
                        if not DirectionHelper.has_wall(model, row, col, direction) or DirectionHelper.is_wall_destroyed(model, row, col, direction):
                            has_access = True
                            break
                    
                    if not has_access:
                        continue
                    
                    # Add to valid cells list
                    valid_cells.append((row, col))
            
            # If no valid cells found
            if not valid_cells:
                model.mazo_pois.append(poi_type)
                model.random.shuffle(model.mazo_pois)
                continue
                
            # Shuffle the valid cells to add randomness
            model.random.shuffle(valid_cells)
            
            # Try placing POI in a valid cell
            placed = False
            for row, col in valid_cells:
                # Skip if another POI already exists
                if model.grid_state[row, col]["poi"] is not None:
                    continue
                    
                # Check for firefighter in cell
                cell_contents = model.grid.get_cell_list_contents((col, row))
                firefighters = [agent for agent in cell_contents if isinstance(agent, FirefighterAgent)]
                
                # If firefighter and false alarm, skip this cell
                if firefighters and poi_type == "f":
                    continue
                
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
                
                # Handle immediate discovery by firefighter
                if firefighters and poi_type == "v":
                    for ff in firefighters:
                        if not ff.carrying:
                            ff.carrying = True
                            model.grid_state[row, col]["poi"] = None
                            model.scenario["pois"].remove((row, col, poi_type))
                            break
                
                placed = True
                pois_added += 1
                break
                
            if not placed:
                model.mazo_pois.append(poi_type)
                model.random.shuffle(model.mazo_pois)
        
        return pois_added > 0

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
    
class AStarPathfinder:
    def __init__(self, model):
        self.model = model
        self.max_search_time = 0.5  # Límite de 500ms para búsqueda de camino
        self.max_nodes = 1000  # Límite de nodos explorados

    def heuristic(self, start, goal):
        """Distancia Manhattan como heurística"""
        return abs(start[0] - goal[0]) + abs(start[1] - goal[1])

    def get_neighbors(self, pos):
        """Obtiene celdas vecinas válidas considerando paredes, puertas y la opción de romperlas"""
        neighbors = []
        x, y = pos
    
        # Validación de posición actual
        if not (0 <= y < self.model.grid_state.shape[0] and 0 <= x < self.model.grid_state.shape[1]):
            return neighbors
    
        for direction in range(4):
            nx, ny = DirectionHelper.get_adjacent_position(x, y, direction)
            
            # Validación de posición vecina
            if not (0 <= ny < self.model.grid_state.shape[0] and 0 <= nx < self.model.grid_state.shape[1]):
                continue
                
            # Caso 1: Paso libre (sin obstáculos)
            if DirectionHelper.can_pass_wall(self.model, y, x, direction):
                neighbors.append((nx, ny, 0))  # 0 = costo normal
                continue
                
            # Caso 2: Puerta
            if DirectionHelper.is_door(self.model, y, x, direction):
                door_state = DirectionHelper.get_door_state(self.model, y, x, direction)
                if door_state == "closed":
                    neighbors.append((nx, ny, 1))  # 1 AP para abrir
                elif door_state != "destroyed":  # Si no está destruida, se puede romper
                    neighbors.append((nx, ny, 2))  # 2 AP para romper
                    
            # Caso 3: Pared rompible
            elif (DirectionHelper.has_wall(self.model, y, x, direction) and 
                  not DirectionHelper.is_perimeter(self.model, x, y)):
                wall_key = DirectionHelper.get_wall_key(y, x, direction)
                damage = self.model.wall_damage.get(wall_key, 0)
                if damage < 2:  # Si la pared aún no está destruida
                    neighbors.append((nx, ny, 2))  # 2 AP para romper
    
        return neighbors
    
    def find_path(self, start, goal, avoid_fire=True):
        """A* optimizado con límites y caché"""
        import time
        start_time = time.time()
        nodes_explored = 0
        
        # Validación inicial de posiciones
        grid_height, grid_width = self.model.grid_state.shape
        
        if not (0 <= start[0] < grid_width and 0 <= start[1] < grid_height and
                0 <= goal[0] < grid_width and 0 <= goal[1] < grid_height):
            return [], []
        
        # Caché de caminos
        path_key = (start, goal, avoid_fire)
        if hasattr(self, '_path_cache') and path_key in self._path_cache:
            path, actions = self._path_cache[path_key]
            if self._is_path_valid(path):
                return path, actions
        
        # Verificación rápida de distancia
        if self.heuristic(start, goal) > 15:
            return [], []
    
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        action_cost = {start: 0}
        
        while frontier and nodes_explored < self.max_nodes:
            if time.time() - start_time > self.max_search_time:
                return [], []
                
            current = heapq.heappop(frontier)[1]
            nodes_explored += 1
            
            if current == goal:
                break
                
            neighbors = self.get_neighbors(current)
            for next_state in neighbors:
                next_pos = (next_state[0], next_state[1])
                action_ap = next_state[2]
                
                new_cost = cost_so_far[current] + 1 + action_ap
                
                # Penalizaciones optimizadas
                if avoid_fire:
                    cell = self.model.grid_state[next_pos[1]][next_pos[0]]
                    if cell["fire"]:
                        new_cost += 10
                    elif cell["smoke"]:
                        new_cost += 3
                
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    action_cost[next_pos] = action_ap
                    priority = new_cost + self.heuristic(goal, next_pos)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current
        
        # Si no se encontró camino
        if goal not in came_from:
            return [], [], 
            
        # Reconstruir camino
        path = []
        actions = []
        current = goal
        
        while current is not None:
            path.append(current)
            actions.append(action_cost.get(current, 0))
            current = came_from.get(current)
        
        path.reverse()
        actions.reverse()
        
        # Guardar en caché
        if not hasattr(self, '_path_cache'):
            self._path_cache = {}
        self._path_cache[path_key] = (path, actions)
        
        return path, actions
    
    def _is_path_valid(self, path):
        """Verifica si un camino sigue siendo válido"""
        if not path:
            return False
            
        for pos in path:
            x, y = pos
            cell = self.model.grid_state[y][x]
            if cell["fire"]:
                return False
        return True
    
class FirefighterAgent(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(model)
        self.unique_id = unique_id
        self.ap = 4
        self.carrying = False
        self.assigned_entry = None
        self.direction = None
        self.max_ap = 8
        self.pathfinder = AStarPathfinder(model)
        self.current_path = []
        self.current_target = None

    def find_nearest_target(self):
        """Encuentra el objetivo más cercano de manera optimizada"""
        current_pos = self.pos
        grid_height, grid_width = self.model.grid_state.shape[:2]
        
        # Si llevamos víctima, prioridad a la salida más cercana
        if self.carrying:
            entries = sorted(
                self.model.scenario["entries"],
                key=lambda e: abs(e[1] - current_pos[0]) + abs(e[0] - current_pos[1])
            )
            
            for entry in entries[:2]:  # Probar con las 2 salidas más cercanas
                target = (entry[1], entry[0])
                path, actions = self.pathfinder.find_path(current_pos, target, avoid_fire=True)
                if path:
                    return (target[0], target[1], 'exit'), path, actions
            return None, [], []
        
        # Buscar víctimas prioritariamente
        victims = []
        for poi in self.model.scenario["pois"]:
            y, x, poi_type = poi
            if poi_type == 'v':
                dist = abs(x - current_pos[0]) + abs(y - current_pos[1])
                if dist < 8:  # Limitar búsqueda a distancia razonable
                    victims.append((x, y, dist))
        
        # Ordenar víctimas por distancia
        victims.sort(key=lambda v: v[2])
        for x, y, _ in victims[:2]:  # Probar con las 2 víctimas más cercanas
            path, actions = self.pathfinder.find_path(current_pos, (x, y), avoid_fire=True)
            if path:
                return (x, y, 'victim'), path, actions
        
        # Buscar fuego cercano si no hay víctimas accesibles
        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            new_x, new_y = current_pos[0] + dx, current_pos[1] + dy
            if (0 <= new_y < grid_height and 0 <= new_x < grid_width and
                self.model.grid_state[new_y][new_x]["fire"]):
                return (new_x, new_y, 'fire'), [current_pos, (new_x,new_y)], [0, 0]
        
        return None, [], []

    def step(self):
        """Ejecuta un paso del bombero"""
        if self.model.stage == 1 and self.assigned_entry is not None:
            self.model.grid.move_agent(self, self.assigned_entry)
            self.assigned_entry = None
            return
    
        while self.ap > 0:
            if not self.current_path or len(self.current_path) <= 1:
                self.current_target, self.current_path, self.path_actions = self.find_nearest_target()
                if not self.current_target:
                    break
    
            if self.current_path and len(self.current_path) > 1:
                next_pos = self.current_path[1]
                action_cost = self.path_actions[1]
    
                # Primero realizar acción necesaria (romper/abrir)
                if action_cost > 0:
                    success = self._perform_obstacle_action(next_pos)
                    if not success:
                        self.current_path = []
                        continue
    
                # Luego intentar el movimiento
                ap_cost = self._calculate_movement_cost(next_pos)
                if self.ap >= ap_cost:
                    success = self._perform_movement_to(next_pos)
                    if success:
                        self.current_path = self.current_path[1:]
                        self.path_actions = self.path_actions[1:]
                        continue
    
            if self._perform_other_actions():
                self.current_path = []
                self.current_target = None
            else:
                break

    def _calculate_movement_cost(self, next_pos):
        """Calcula el costo de AP para moverse a una posición"""
        dest_cell = self.model.grid_state[next_pos[1]][next_pos[0]]
        ap_cost = 1

        if dest_cell["fire"]:
            ap_cost = 2
        if self.carrying:
            ap_cost = 2

        return ap_cost

    def _perform_movement_to(self, new_pos):
        """Realiza el movimiento a una posición específica""" 
        if not (0 <= new_pos[1] < self.model.grid.height and
                0 <= new_pos[0] < self.model.grid.width):
            return False

        original_pos = self.pos
        ap_cost = self._calculate_movement_cost(new_pos)

        if self.ap >= ap_cost:
            self.model.grid.move_agent(self, new_pos)
            self.ap -= ap_cost
            return True
        return False

    def _perform_other_actions(self):
        """Realiza otras acciones como extinguir fuego o recoger víctimas"""
        x, y = self.pos
        cell = self.model.grid_state[y][x]

        # 1. Recoger víctima
        if not self.carrying and cell["poi"] == "v" and self.ap >= 2:
            self.carrying = True
            cell["poi"] = None
            for i, poi in enumerate(self.model.scenario["pois"]):
                if poi[0] == y and poi[1] == x:
                    self.model.scenario["pois"].pop(i)
                    break
            self.ap -= 2
            return True

        # 2. Dejar víctima en entrada
        entradas = [(e[1], e[0]) for e in self.model.scenario["entries"]]
        if self.carrying and (x, y) in entradas:
            self.carrying = False
            self.model.victims_rescued += 1
            self.ap = 0
            return True

        # 3. Apagar fuego
        if cell["fire"] and self.ap >= 2:
            cell["fire"] = False
            cell["smoke"] = True
            if (y, x) in self.model.scenario["fires"]:
                self.model.scenario["fires"].remove((y, x))
            self.ap -= 2
            return True

        # 4. Eliminar humo
        if cell["smoke"] and self.ap >= 2:
            cell["smoke"] = False
            self.ap -= 2
            return True

        # 5. Falsa alarma
        if cell["poi"] == "f":
            cell["poi"] = None
            for i, poi in enumerate(self.model.scenario["pois"]):
                if poi[0] == y and poi[1] == x:
                    self.model.scenario["pois"].pop(i)
                    break
            self.ap = 0
            return True

        # 6. Operaciones con puertas
        for direction in range(4):
            if DirectionHelper.is_door(self.model, y, x, direction) and self.ap >= 1:
                door_state = DirectionHelper.get_door_state(self.model, y, x, direction)
                if door_state in ["open", "closed"]:
                    new_state = "closed" if door_state == "open" else "open"
                    self.model.door_states[(y, x, direction)] = new_state
                    self.ap -= 1
                    return True

        # 7. Operaciones con paredes
        for direction in range(4):
            if (DirectionHelper.has_wall(self.model, y, x, direction) and 
                not DirectionHelper.is_perimeter(self.model, x, y) and 
                self.ap >= 2):
                if DirectionHelper.damage_wall(self.model, y, x, direction):
                    self.ap -= 2
                    return True

        # Si ninguna acción se realizó
        return False

    def _perform_obstacle_action(self, next_pos):
        """Realiza acciones para superar obstáculos (romper paredes/abrir puertas)"""
        current_x, current_y = self.pos
        next_x, next_y = next_pos
    
        # Determinar dirección del movimiento
        dx = next_x - current_x
        dy = next_y - current_y
        
        # Convertir diferencia a dirección
        direction = None
        if dx == 1: direction = DirectionHelper.EAST
        elif dx == -1: direction = DirectionHelper.WEST
        elif dy == 1: direction = DirectionHelper.SOUTH
        elif dy == -1: direction = DirectionHelper.NORTH
    
        if direction is None:
            return False
    
        # Verificar si hay una puerta
        if DirectionHelper.is_door(self.model, current_y, current_x, direction):
            door_state = DirectionHelper.get_door_state(self.model, current_y, current_x, direction)
            if door_state == "closed" and self.ap >= 1:
                # Abrir puerta
                self.model.door_states[(current_y, current_x, direction)] = "open"
                self.ap -= 1
                return True
    
        # Verificar si hay una pared rompible
        if (DirectionHelper.has_wall(self.model, current_y, current_x, direction) and 
            not DirectionHelper.is_perimeter(self.model, current_x, current_y) and 
            self.ap >= 2):
            # Romper pared
            if DirectionHelper.damage_wall(self.model, current_y, current_x, direction):
                self.ap -= 2
                return True
    
        return False

class FireRescueModel(Model):
    """Fire rescue simulation model"""

    def __init__(self, scenario):
        super().__init__()

        # Build grid state first to get correct dimensions
        self.grid_state = ScenarioParser.build_grid_state(scenario)
        grid_height, grid_width = self.grid_state.shape

        # Initialize grid with same dimensions as grid_state
        self.grid = MultiGrid(grid_width, grid_height, True)
        self.schedule = RandomActivation(self)
        self.scenario = scenario
        self.door_states = {}

        # Initialize remaining attributes...
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
        ##self.json_exporter = JSONExporter()

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
    
        self.step_count += 1

        if self.stage == 0:
            self.stage = 1
    
        # Ejecutar acciones de los bomberos
        for agent in self.schedule.agents:
            agent.step()
            
        # Fase de propagación del fuego
        if self.step_count > 1:
            GameMechanics.advance_fire(self)
            GameMechanics.check_firefighters_in_fire(self)
            
        # Recuperación de AP
        for agent in self.schedule.agents:
            agent.ap = min(agent.ap + 4, agent.max_ap)
    
        # Reposición de POIs
        GameMechanics.replenish_pois(self)
           
        # Condiciones de fin de juego
        GameMechanics.check_end_conditions(self)

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
    def print_grid_state(model):
        """Prints the current state of the grid in terminal"""
        print("\n" + "="*50)
        print(f"TURNO {model.step_count}")
        print("="*50)
        
        # Estado del juego
        print(f"Víctimas Rescatadas: {model.victims_rescued}")
        print(f"Víctimas Perdidas: {model.victims_lost}")
        print(f"Daño Estructural: {model.damage_counters}/24\n")
        
        # Obtener posiciones de bomberos
        firefighter_positions = {}
        for agent in model.schedule.agents:
            firefighter_positions[agent.pos] = f"B{agent.unique_id}"
        
        # Imprimir grid
        for y in range(model.grid.height):
            row = ""
            for x in range(model.grid.width):
                pos = (x, y)
                cell = model.grid_state[y][x]
                
                if pos in firefighter_positions:
                    row += f"{firefighter_positions[pos]:^3}"
                elif cell["fire"]:
                    row += " F "
                elif cell["smoke"]:
                    row += " S "
                elif cell["poi"] == "v":
                    row += " V "
                elif cell["poi"] == "f":
                    row += " X "
                elif cell["door"]:
                    row += " D "
                elif DirectionHelper.is_entry(model, x, y):
                    row += " E "
                elif any(cell["walls"]):
                    row += " # "
                else:
                    row += " . "
            print(row)
        print()
        
        # Estado de bomberos
        print("ESTADO DE BOMBEROS:")
        for agent in model.schedule.agents:
            status = "Con víctima" if agent.carrying else "Sin víctima"
            x, y = agent.pos
            conditions = []
            if model.grid_state[y][x]["fire"]: conditions.append("FUEGO")
            if model.grid_state[y][x]["smoke"]: conditions.append("HUMO")
            cell_state = f"[{', '.join(conditions)}]" if conditions else ""
            print(f"Bombero {agent.unique_id}: Pos({x},{y}) | AP: {agent.ap}/{agent.max_ap} | {status} {cell_state}")

    @staticmethod
    def visualize_simulation(model):
        """Visualizes the current state of the simulation in both terminal and graphics"""
        # Primero mostrar estado en terminal
        Visualization.print_grid_state(model)
        
        # Luego mostrar visualización gráfica
        fig, ax = Visualization.visualize_grid_with_perimeter_and_doors(
            model.scenario["grid_walls"],
            ScenarioParser.compute_door_positions(model.scenario["doors"]),
            model.scenario["entries"],
            model.scenario["fires"],
            model.scenario["pois"],
            model
        )
        plt.show()


# Añade estas funciones de ayuda
class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# Modifica la función run_multiple_simulations
def run_multiple_simulations(num_simulations=1000, timeout_seconds=1):
    """
    Ejecuta múltiples simulaciones y guarda los resultados en CSV
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"simulation_results_{timestamp}.csv"
    
    headers = ['simulation_id', 'result', 'total_turns', 'victims_rescued', 
              'victims_lost', 'structural_damage']

    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        
        for sim_id in range(num_simulations):
            try:
                with time_limit(timeout_seconds):
                    # Parse scenario and initialize model
                    scenario = ScenarioParser.parse_scenario(scenario_content)
                    model = FireRescueModel(scenario)
                    
                    step = 1
                    while not model.simulation_over and step < 50:
                        model.step()
                        step += 1
                    
                    # Determinar resultado
                    if model.victims_rescued >= 7:
                        result = "VICTORIA"
                    elif model.victims_lost >= 4:
                        result = "DERROTA_VICTIMAS"
                    else:
                        result = "DERROTA_ESTRUCTURAL"
                    
                    writer.writerow({
                        'simulation_id': sim_id + 1,
                        'result': result,
                        'total_turns': step - 1,
                        'victims_rescued': model.victims_rescued,
                        'victims_lost': model.victims_lost,
                        'structural_damage': model.damage_counters
                    })
            
            except TimeoutException:
                writer.writerow({
                    'simulation_id': sim_id + 1,
                    'result': "TIMEOUT",
                    'total_turns': -1,
                    'victims_rescued': -1,
                    'victims_lost': -1,
                    'structural_damage': -1
                })
                print(f"Simulation {sim_id + 1} timed out")
                
            except Exception as e:
                print(f"Error in simulation {sim_id + 1}: {str(e)}")
                writer.writerow({
                    'simulation_id': sim_id + 1,
                    'result': 'ERROR',
                    'total_turns': -1,
                    'victims_rescued': -1,
                    'victims_lost': -1,
                    'structural_damage': -1
                })
            
            # Imprimir progreso cada 100 simulaciones
            if (sim_id + 1) % 100 == 0:
                print(f"Completed {sim_id + 1}/{num_simulations} simulations")
    
    print(f"\nSimulations complete. Results saved to {csv_filename}")

if __name__ == "__main__":
    run_multiple_simulations(1000, timeout_seconds=1)