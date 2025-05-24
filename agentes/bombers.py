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

    # Clase auxiliar para manejo de direcciones, muros y puertas
class DirectionHelper:
    # Constantes para las direcciones
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    
    # Vectores de desplazamiento para cada dirección (dx, dy)
    DIRECTIONS = [
        (0, -1),  # Norte: sin cambio en x, -1 en y
        (1, 0),   # Este: +1 en x, sin cambio en y
        (0, 1),   # Sur: sin cambio en x, +1 en y
        (-1, 0)   # Oeste: -1 en x, sin cambio en y
    ]
    
    # Nombres de las direcciones para mensajes
    DIRECTION_NAMES = ["norte", "este", "sur", "oeste"]
    
    @staticmethod
    def get_adjacent_position(x, y, direction):
        """Obtiene la posición adyacente en la dirección especificada"""
        dx, dy = DirectionHelper.DIRECTIONS[direction]
        return x + dx, y + dy
    
    @staticmethod
    def get_opposite_direction(direction):
        """Obtiene la dirección opuesta (0↔2, 1↔3)"""
        return (direction + 2) % 4
    
    @staticmethod
    def is_perimeter(model, x, y):
        """Verifica si una posición está en el perímetro"""
        return (x == 0 or x == model.grid.width - 1 or y == 0 or y == model.grid.height - 1)
    
    @staticmethod
    def get_wall_key(y, x, direction):
        """Obtiene la clave para un muro en la dirección especificada"""
        return (y, x, direction)
    
    @staticmethod
    def has_wall(model, y, x, direction):
        """Verifica si hay un muro en la dirección especificada"""
        # Verificar si hay muro en la celda actual
        return model.grid_state[y, x]["walls"][direction] == 1
    
    @staticmethod
    def is_wall_destroyed(model, y, x, direction):
        """Verifica si un muro está destruido (tiene 2 o más daños)"""
        wall_key = DirectionHelper.get_wall_key(y, x, direction)
        return wall_key in model.wall_damage and model.wall_damage[wall_key] >= 2
    
    @staticmethod
    def can_pass_wall(model, y, x, direction):
        """Verifica si se puede pasar a través de un muro (no hay muro o está destruido)"""
        return not DirectionHelper.has_wall(model, y, x, direction) or DirectionHelper.is_wall_destroyed(model, y, x, direction)
    
    @staticmethod
    def is_door(model, y, x, direction):
        """Verifica si hay una puerta en la dirección especificada"""
        door_positions = compute_door_positions(model.scenario["doors"])
        door_key = (y, x, direction)
        return door_key in door_positions
    
    @staticmethod
    def get_door_state(model, y, x, direction):
        """Obtiene el estado de una puerta (abierta/cerrada/destruida)"""
        door_key = (y, x, direction)
        
        if door_key not in compute_door_positions(model.scenario["doors"]):
            return None  # No es una puerta
        
        if door_key in model.door_states:
            return model.door_states[door_key]  # "abierta" o "cerrada"
        else:
            return "destruida"  # Si no está en door_states pero es una puerta, está destruida
    
    @staticmethod
    def is_entry(model, x, y):
        """Verifica si una posición es una entrada"""
        return (x, y) in [(e[1], e[0]) for e in model.scenario["entries"]]
    
    @staticmethod
    def damage_wall(model, y, x, direction):
        """Añade un punto de daño a un muro y verifica si se destruye"""
        wall_key = DirectionHelper.get_wall_key(y, x, direction)
        
        # Añadir daño
        if wall_key not in model.wall_damage:
            model.wall_damage[wall_key] = 1
        else:
            model.wall_damage[wall_key] += 1
        
        model.damage_counters += 1
        
        # Si el muro tiene 2 daños, se destruye
        if model.wall_damage[wall_key] >= 2:
            # Destruir el muro en la celda actual
            model.grid_state[y, x]["walls"][direction] = 0
            
            # También destruir el muro correspondiente en la celda adyacente
            new_x, new_y = DirectionHelper.get_adjacent_position(x, y, direction)
            opposite_direction = DirectionHelper.get_opposite_direction(direction)
            
            # Verificar que la celda adyacente esté dentro de los límites
            if 0 <= new_y < model.grid.height and 0 <= new_x < model.grid.width:
                model.grid_state[new_y, new_x]["walls"][opposite_direction] = 0
                
            return True  # Muro destruido
        
        return False  # Muro dañado pero no destruido


def parse_grid_walls(lines):
    """Parsea las 6 primeras líneas del escenario para obtener los muros"""
    original_grid = np.zeros((6, 8, 4), dtype=int)
    for i, line in enumerate(lines[:6]):
        for j, cell in enumerate(line.strip().split()):
            original_grid[i, j] = [int(d) for d in cell]
    
    # Crear grid extendido con perímetro (8, 10, 4)
    grid = np.zeros((8, 10, 4), dtype=int)

    # Copiar escenario original en centro (1:7, 1:9)
    grid[1:7, 1:9] = original_grid

    # Agregar muros en el perímetro externo
    grid[0, 1:9, 0] = 1  # Norte
    grid[7, 1:9, 2] = 1  # Sur
    grid[1:7, 0, 3] = 1  # Oeste
    grid[1:7, 9, 1] = 1  # Este
    
    print("Muros parseados correctamente.")
    return grid

def parse_pois(lines):
    """Parsea las líneas de Puntos de Interés (POI)"""
    pois = []
    poi_lines = lines[6:9]  # 3 líneas después de los muros
    
    for line in poi_lines:
        parts = line.strip().split()
        if len(parts) == 3:
            row, col, poi_type = parts
            # Convertir a coordenadas 0-based y considerar perímetro (+1)
            row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
            pois.append((row_idx, col_idx, poi_type))
    
    print(f"POIs parseados: {pois}")
    return pois

def parse_fires(lines):
    """Parsea las líneas de fuego inicial"""
    fires = []
    fire_lines = lines[9:19]  # 10 líneas después de los POIs
    
    for line in fire_lines:
        parts = line.strip().split()
        if len(parts) == 2:
            row, col = parts
            # Convertir a coordenadas 0-based y considerar perímetro (+1)
            row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
            fires.append((row_idx, col_idx))
    
    print(f"Fuegos iniciales parseados: {fires}")
    return fires

def parse_doors(lines):
    """Parsea las líneas de puertas"""
    doors = []
    door_lines = lines[19:27]  # 8 líneas después de los fuegos
    
    for line in door_lines:
        parts = line.strip().split()
        if len(parts) == 4:
            r1, c1, r2, c2 = parts
            # Convertir a coordenadas 0-based y considerar perímetro (+1)
            r1_idx, c1_idx = int(r1) - 1 + 1, int(c1) - 1 + 1
            r2_idx, c2_idx = int(r2) - 1 + 1, int(c2) - 1 + 1
            doors.append(((r1_idx, c1_idx), (r2_idx, c2_idx)))
    
    print(f"Puertas parseadas: {doors}")
    return doors

def parse_entries(lines):
    """Parsea las líneas de entradas de bomberos"""
    entries = []
    entry_lines = lines[27:31]  # 4 líneas después de las puertas
    
    for line in entry_lines:
        parts = line.strip().split()
        if len(parts) == 2:
            row, col = parts
            # Convertir a coordenadas 0-based y considerar perímetro (+1)
            row_idx, col_idx = int(row) - 1 + 1, int(col) - 1 + 1
            entries.append((row_idx, col_idx))
    
    print(f"Entradas parseadas: {entries}")
    return entries

def parse_scenario(scenario_text):
    """Función principal que parsea todo el contenido del escenario"""
    lines = scenario_text.strip().split('\n')
    
    # Validar que haya suficientes líneas
    if len(lines) < 31:
        print(f"Error: El escenario debe tener al menos 31 líneas, tiene {len(lines)}")
        return None
    
    # Parsear cada componente
    grid = parse_grid_walls(lines)
    pois = parse_pois(lines)
    fires = parse_fires(lines)
    doors = parse_doors(lines)
    entries = parse_entries(lines)
    
    # Crear diccionario de escenario
    scenario = {
        "grid_walls": grid,
        "pois": pois,
        "fires": fires,
        "doors": doors,
        "entries": entries
    }
    
    print("Escenario parseado completamente.")
    return scenario

def compute_door_positions(doors):
    """Calcula las posiciones de las puertas para la visualización"""
    door_positions = []
    for (r1, c1), (r2, c2) in doors:
        # Determinar en qué dirección está la puerta
        if r1 == r2:  # Puerta horizontal (este-oeste)
            if c1 < c2:  # c1 está a la izquierda de c2
                door_positions.append((r1, c1, 1))  # Puerta en el este de celda 1
            else:
                door_positions.append((r1, c2, 1))  # Puerta en el este de celda 2
        else:  # Puerta vertical (norte-sur)
            if r1 < r2:  # r1 está arriba de r2
                door_positions.append((r1, c1, 2))  # Puerta en el sur de celda 1
            else:
                door_positions.append((r2, c2, 2))  # Puerta en el sur de celda 2
    
    return door_positions

def build_grid_state(scenario):
    """Construye una matriz de celdas donde cada celda es un diccionario con estado completo"""
    filas, columnas = scenario["grid_walls"].shape[:2]
    
    # Crear matriz vacía
    grid_state = np.empty((filas, columnas), dtype=object)
    
    # Calcular posiciones de puertas para identificar celdas con puertas
    door_positions = compute_door_positions(scenario["doors"])
    
    # Inicializar cada celda
    for y in range(filas):
        for x in range(columnas):
            # Obtener información de muros
            walls = scenario["grid_walls"][y, x].tolist()
            
            # Verificar si hay fuego
            fire = (y, x) in scenario["fires"]
            
            # Verificar si hay puerta en alguna dirección
            door = any((y, x, d) in door_positions for d in range(4))
            
            # Verificar si hay POI y de qué tipo
            poi = None
            for p_y, p_x, p_type in scenario["pois"]:
                if p_y == y and p_x == x:
                    poi = p_type
                    break
            
            # Crear diccionario de celda
            cell = {
                "walls": walls,
                "fire": fire,
                "smoke": False,
                "damage": 0,
                "door": door,
                "poi": poi
            }
            
            # Asignar a la matriz
            grid_state[y, x] = cell
    
    return grid_state

def print_cell_info(grid_state, y, x):
    """Imprime información detallada de una celda para verificación"""
    cell = grid_state[y, x]
    print(f"Celda ({y}, {x}):")
    print(f"  Muros (NESO): {cell['walls']}")
    print(f"  Fuego: {cell['fire']}")
    print(f"  Humo: {cell['smoke']}")
    print(f"  Daño: {cell['damage']}")
    print(f"  Puerta: {cell['door']}")
    print(f"  POI: {cell['poi']}")
    print()

def verify_grid_state(grid_state):
    """Verifica que algunas celdas estén correctamente inicializadas"""
    filas, columnas = grid_state.shape
    
    # Verificar las esquinas
    print("=== ESQUINAS ===")
    print_cell_info(grid_state, 0, 0)             # Esquina superior izquierda
    print_cell_info(grid_state, 0, columnas-1)    # Esquina superior derecha
    print_cell_info(grid_state, filas-1, 0)       # Esquina inferior izquierda
    print_cell_info(grid_state, filas-1, columnas-1)  # Esquina inferior derecha
    
    # Verificar algunas celdas con características especiales
    print("=== CELDAS INTERIORES ===")
    
    # Buscar una celda con fuego
    for y in range(filas):
        for x in range(columnas):
            if grid_state[y, x]["fire"]:
                print("Celda con FUEGO:")
                print_cell_info(grid_state, y, x)
                break
    
    # Buscar una celda con puerta
    for y in range(filas):
        for x in range(columnas):
            if grid_state[y, x]["door"]:
                print("Celda con PUERTA:")
                print_cell_info(grid_state, y, x)
                break
    
    # Buscar una celda con POI
    for y in range(filas):
        for x in range(columnas):
            if grid_state[y, x]["poi"] is not None:
                print(f"Celda con POI (tipo {grid_state[y, x]['poi']}):")
                print_cell_info(grid_state, y, x)
                break

# Función de visualización 
def visualizar_grid_con_perimetro_y_puertas(grid, door_positions, entries, fires=None, pois=None, model=None):
    filas, columnas = grid.shape[:2]
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_facecolor('#d9f2d9')  # Fondo verde claro

    # Determinar la dirección de cada entrada (hacia el borde más cercano)
    entry_positions = []
    for y, x in entries:
        # Determinar qué borde está más cerca
        dist_norte = y
        dist_sur = filas - 1 - y
        dist_oeste = x
        dist_este = columnas - 1 - x
        
        # La dirección con la distancia mínima es la más cercana al borde
        min_dist = min(dist_norte, dist_sur, dist_oeste, dist_este)
        
        if min_dist == dist_norte:
            entry_positions.append((y, x, 0))  # Norte
        elif min_dist == dist_este:
            entry_positions.append((y, x, 1))  # Este
        elif min_dist == dist_sur:
            entry_positions.append((y, x, 2))  # Sur
        else:  # min_dist == dist_oeste
            entry_positions.append((y, x, 3))  # Oeste

    for y in range(filas):
        for x in range(columnas):
            # Verificar si hay fuego o humo en esta celda
            is_fire = (y, x) in fires if fires else False
            is_smoke = False
            
            if model is not None:
                # Usar grid_state para detectar humo
                is_smoke = model.grid_state[y, x]["smoke"]
            
            # Determinar el color de fondo según la celda
            if is_fire:
                color = '#ffcccc'  # Color rojizo claro para fuego
            elif is_smoke:
                color = '#e6e6e6'  # Color gris claro para humo
            elif x == 0 or x == columnas-1 or y == 0 or y == filas-1:
                color = '#b3e6b3'  # Color verde claro para perímetro
            else:
                color = '#e6f7ff'  # Color azul claro para celdas jugables
                
            rect = patches.Rectangle((x, filas - y - 1), 1, 1, linewidth=0, facecolor=color)
            ax.add_patch(rect)

            # Dibujar líneas de cuadrícula claras
            ax.plot([x, x+1], [filas - y - 1, filas - y - 1], color='gray', linewidth=0.3)
            ax.plot([x, x+1], [filas - y, filas - y], color='gray', linewidth=0.3)
            ax.plot([x, x], [filas - y - 1, filas - y], color='gray', linewidth=0.3)
            ax.plot([x+1, x+1], [filas - y - 1, filas - y], color='gray', linewidth=0.3)

            # Dibujar símbolos para fuego si corresponde
            if is_fire:
                ax.plot(x + 0.5, filas - y - 0.5, 'o', markersize=15, 
                        markerfacecolor='#ff6600', markeredgecolor='red', alpha=0.7)
                ax.plot(x + 0.5, filas - y - 0.5, '*', markersize=10, 
                        markerfacecolor='yellow', markeredgecolor='yellow')
            
            # Dibujar símbolos para humo si corresponde
            elif is_smoke:
                ax.plot(x + 0.5, filas - y - 0.5, 's', markersize=14, 
                        markerfacecolor='#a6a6a6', markeredgecolor='#808080', alpha=0.6)
                ax.plot(x + 0.5, filas - y - 0.5, 'o', markersize=8, 
                        markerfacecolor='#d3d3d3', markeredgecolor='#d3d3d3', alpha=0.8)

            # Verificar si hay un POI en esta posición
            if pois:
                for poi_y, poi_x, poi_type in pois:
                    if poi_y == y and poi_x == x:
                        if poi_type == 'v':  # Víctima
                            ax.plot(x + 0.5, filas - y - 0.5, 'D', markersize=12, 
                                    markerfacecolor='#00cc66', markeredgecolor='black', zorder=10)
                        elif poi_type == 'f':  # Falsa alarma
                            ax.plot(x + 0.5, filas - y - 0.5, 'X', markersize=12, 
                                    markerfacecolor='#cccccc', markeredgecolor='black', zorder=10)
                            
            # Determinar si es una celda de perímetro
            es_perimetro = (x == 0 or x == columnas-1 or y == 0 or y == filas-1)

            if es_perimetro:
                # Solo dibujamos los muros del perímetro exterior
                if y == 0:
                    ax.plot([x, x+1], [filas - y, filas - y], color='black', linewidth=2.5)
                if y == filas-1:
                    ax.plot([x, x+1], [filas - y - 1, filas - y - 1], color='black', linewidth=2.5)
                if x == 0:
                    ax.plot([x, x], [filas - y - 1, filas - y], color='black', linewidth=2.5)
                if x == columnas-1:
                    ax.plot([x+1, x+1], [filas - y - 1, filas - y], color='black', linewidth=2.5)
            else:
                # CAMBIO: Usar grid_state en lugar de grid para los muros
                if model is not None:
                    muro_n, muro_e, muro_s, muro_o = model.grid_state[y, x]["walls"]
                else:
                    muro_n, muro_e, muro_s, muro_o = grid[y, x]

                # Comprobar si hay una puerta o entrada en cada dirección
                puerta_n = (y, x, 0) in door_positions
                puerta_e = (y, x, 1) in door_positions
                puerta_s = (y, x, 2) in door_positions
                puerta_o = (y, x, 3) in door_positions
                
                entrada_n = (y, x, 0) in entry_positions
                entrada_e = (y, x, 1) in entry_positions
                entrada_s = (y, x, 2) in entry_positions
                entrada_o = (y, x, 3) in entry_positions

                # Dibujar muros, puertas o entradas según corresponda
                if entrada_n:
                    # Dibujar entrada norte
                    ax.plot([x+0.25, x+0.75], [filas - y, filas - y], color='white', linewidth=4.0)
                elif puerta_n:
                    # Dibujar puerta norte según su estado
                    puerta_color = 'brown'
                    puerta_abierta = False
                    if model is not None and (y, x, 0) in model.door_states:
                        puerta_abierta = model.door_states[(y, x, 0)] == "abierta"
                        puerta_color = 'green' if puerta_abierta else 'brown'
                    else:
                        # Si no está en door_states pero es una puerta, se considera destruida
                        if model is not None:
                            puerta_color = 'lightgreen'  # Color distintivo para puertas destruidas
                    ax.plot([x+0.25, x+0.75], [filas - y, filas - y], color=puerta_color, linewidth=2.5)
                elif muro_n:
                    # Dibujar muro norte
                    muro_color = 'black'
                    if model is not None and (y, x, 0) in model.wall_damage:
                        # Si el muro tiene daño, cambiar color
                        if model.wall_damage[(y, x, 0)] == 1:
                            muro_color = 'orange'  # Muro dañado una vez
                        # Si tiene 2 daños, no se dibuja (está destruido)
                        elif model.wall_damage[(y, x, 0)] >= 2:
                            muro_color = None  # No dibujar
                    
                    if muro_color:
                        ax.plot([x, x+1], [filas - y, filas - y], color=muro_color, linewidth=2.5)
                
                # Para las puertas en dirección Este:
                if entrada_e:
                    # Dibujar entrada este
                    ax.plot([x+1, x+1], [filas - y - 0.75, filas - y - 0.25], color='white', linewidth=4.0)
                elif puerta_e:
                    # Dibujar puerta este según su estado
                    puerta_color = 'brown'
                    if model is not None and (y, x, 1) in model.door_states:
                        puerta_abierta = model.door_states[(y, x, 1)] == "abierta"
                        puerta_color = 'green' if puerta_abierta else 'brown'
                    else:
                        # Si no está en door_states pero es una puerta, se considera destruida
                        if model is not None:
                            puerta_color = 'lightgreen'  # Color distintivo para puertas destruidas
                    ax.plot([x+1, x+1], [filas - y - 0.75, filas - y - 0.25], color=puerta_color, linewidth=2.5)
                elif muro_e:
                    # Dibujar muro este
                    muro_color = 'black'
                    if model is not None and (y, x, 1) in model.wall_damage:
                        # Si el muro tiene daño, cambiar color
                        if model.wall_damage[(y, x, 1)] == 1:
                            muro_color = 'orange'
                        elif model.wall_damage[(y, x, 1)] >= 2:
                            muro_color = None
                    
                    if muro_color:
                        ax.plot([x+1, x+1], [filas - y - 1, filas - y], color=muro_color, linewidth=2.5)
                
                # Para las puertas en dirección Sur:
                if entrada_s:
                    # Dibujar entrada sur
                    ax.plot([x+0.25, x+0.75], [filas - y - 1, filas - y - 1], color='white', linewidth=4.0)
                elif puerta_s:
                    # Dibujar puerta sur según su estado
                    puerta_color = 'brown'
                    if model is not None and (y, x, 2) in model.door_states:
                        puerta_abierta = model.door_states[(y, x, 2)] == "abierta"
                        puerta_color = 'green' if puerta_abierta else 'brown'
                    else:
                        # Si no está en door_states pero es una puerta, se considera destruida
                        if model is not None:
                            puerta_color = 'lightgreen'  # Color distintivo para puertas destruidas
                    ax.plot([x+0.25, x+0.75], [filas - y - 1, filas - y - 1], color=puerta_color, linewidth=2.5)
                elif muro_s:
                    # Dibujar muro sur
                    muro_color = 'black'
                    if model is not None and (y, x, 2) in model.wall_damage:
                        # Si el muro tiene daño, cambiar color
                        if model.wall_damage[(y, x, 2)] == 1:
                            muro_color = 'orange'
                        elif model.wall_damage[(y, x, 2)] >= 2:
                            muro_color = None
                    
                    if muro_color:
                        ax.plot([x, x+1], [filas - y - 1, filas - y - 1], color=muro_color, linewidth=2.5)
                
                if entrada_o:
                    # Dibujar entrada oeste
                    ax.plot([x, x], [filas - y - 0.75, filas - y - 0.25], color='white', linewidth=4.0)
                elif puerta_o:
                    # Dibujar puerta oeste según su estado
                    puerta_color = 'brown'
                    if model is not None and (y, x, 3) in model.door_states:
                        puerta_abierta = model.door_states[(y, x, 3)] == "abierta"
                        puerta_color = 'green' if puerta_abierta else 'brown'
                    else:
                        # Si no está en door_states pero es una puerta, se considera destruida
                        if model is not None:
                            puerta_color = 'lightgreen'  # Color distintivo para puertas destruidas
                    ax.plot([x, x], [filas - y - 0.75, filas - y - 0.25], color=puerta_color, linewidth=2.5)
                elif muro_o:
                    # Dibujar muro oeste
                    muro_color = 'black'
                    if model is not None and (y, x, 3) in model.wall_damage:
                        # Si el muro tiene daño, cambiar color
                        if model.wall_damage[(y, x, 3)] == 1:
                            muro_color = 'orange'
                        elif model.wall_damage[(y, x, 3)] >= 2:
                            muro_color = None
                    
                    if muro_color:
                        ax.plot([x, x], [filas - y - 1, filas - y], color=muro_color, linewidth=2.5)
                    
    # Agregar elementos a la leyenda
    entrada_line = plt.Line2D([0], [0], color='white', linewidth=4.0, label='Entrada bomberos')
    perimetro_patch = patches.Patch(color='#b3e6b3', label='Perímetro')
    jugable_patch = patches.Patch(color='#e6f7ff', label='Celda jugable')
    puerta_line = plt.Line2D([0], [0], color='brown', linewidth=2.5, label='Puerta')
    muro_line = plt.Line2D([0], [0], color='black', linewidth=2.5, label='Muro')
    
    # Nuevos elementos para la leyenda
    fire_marker = plt.Line2D([0], [0], marker='o', markersize=15, markerfacecolor='#ff6600', 
                            markeredgecolor='red', alpha=0.7, linestyle='', label='Fuego')
    smoke_marker = plt.Line2D([0], [0], marker='s', markersize=14, markerfacecolor='#a6a6a6', 
                            markeredgecolor='#808080', alpha=0.6, linestyle='', label='Humo')
    victim_marker = plt.Line2D([0], [0], marker='D', markersize=12, markerfacecolor='#00cc66', 
                            markeredgecolor='black', linestyle='', label='Víctima (POI)')
    false_alarm_marker = plt.Line2D([0], [0], marker='X', markersize=12, markerfacecolor='#cccccc', 
                            markeredgecolor='black', linestyle='', label='Falsa alarma (POI)')
    
    ax.legend(handles=[perimetro_patch, jugable_patch, entrada_line, muro_line, puerta_line, 
                    fire_marker, smoke_marker, victim_marker, false_alarm_marker], 
            loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)



    if model is not None:
        # Agregar bomberos a la leyenda
        bombero_marker = plt.Line2D([0], [0], marker='o', markersize=15, 
                                  markerfacecolor='blue', markeredgecolor='navy', 
                                  alpha=0.7, linestyle='', label='Bombero')
        
        # Actualizar la leyenda para incluir bomberos
        ax.legend(handles=[perimetro_patch, jugable_patch, entrada_line, muro_line, 
                          puerta_line, fire_marker, victim_marker, false_alarm_marker,
                          bombero_marker], 
                  loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
        
        # Configurar límites para ver TODA el área, incluido el exterior
        ax.set_xlim(-1, columnas+1) 
        ax.set_ylim(-1, filas+1)
        
        # Dibujar bomberos como círculos azules con número de identificación
        for agent in model.schedule.agents:
            x, y = agent.pos  # Mesa usa (x=columna, y=fila)
            # Dibujamos bomberos con coordenadas ajustadas
            ax.plot(x + 0.5, filas - y - 0.5, 'o', markersize=24, 
                    markerfacecolor='blue', markeredgecolor='navy', alpha=0.7, zorder=25)
            ax.text(x + 0.5, filas - y - 0.5, str(agent.unique_id), color='white', 
                    fontsize=12, ha='center', va='center', zorder=26)
        
        # Actualizar título si hay un modelo
        ax.set_title(f"Simulación - Paso {model.step_count}")
    
    # Aspecto visual 
    ax.set_xticks(range(columnas))
    ax.set_yticks(range(filas))
    ax.set_xticklabels(range(columnas))
    ax.set_yticklabels(range(filas - 1, -1, -1))
    ax.set_aspect('equal')
    
    # NO fijar estos límites, pues restringen la visualización de los bomberos
    # ax.set_xlim(0, columnas) 
    # ax.set_ylim(0, filas)
    
    # IMPORTANTE: Actualizar el título para reflejar el paso actual
    if model is not None:
        ax.set_title(f"Simulación - Paso {model.step_count}")
    else:
        ax.set_title("Mapa del Escenario 6×8 con Perímetro (8×10), Muros y Puertas")
    
    ax.grid(False)
    plt.tight_layout()
    plt.show()

# Agregar después de la función visualizar_grid_con_perimetro_y_puertas y antes de la definición de clases
def advance_fire(model):
    """Propaga el fuego a través del escenario según las reglas del juego Flash Point: Fire Rescue"""
    filas, columnas = model.grid_state.shape
    
    # Inicializar contadores si no existen
    if not hasattr(model, 'victims_lost'):
        model.victims_lost = 0
    if not hasattr(model, 'damage_counters'):
        model.damage_counters = 0
    
    # 1. SIMULAR TIRADA DE DADOS PARA AGREGAR FUEGO ALEATORIO
    # Generar coordenadas aleatorias válidas (no en el perímetro)
    fila_aleatoria = model.random.randint(1, filas-2)
    columna_aleatoria = model.random.randint(1, columnas-2)
    
    # Verificar el estado de la celda aleatoria
    celda = model.grid_state[fila_aleatoria, columna_aleatoria]
    
    print(f"🎲 Tirada de dados: Punto de ignición en ({columna_aleatoria},{fila_aleatoria})")
    
    # Caso 1: Celda sin fuego ni humo -> Agregar fuego
    if not celda["fire"] and not celda["smoke"]:
        celda["fire"] = True
        if (fila_aleatoria, columna_aleatoria) not in model.scenario["fires"]:
            model.scenario["fires"].append((fila_aleatoria, columna_aleatoria))
        print(f"🔥 Fuego añadido en ({columna_aleatoria},{fila_aleatoria})")
        
        # Verificar si hay víctima en la celda
        if celda["poi"] == "v":
            celda["poi"] = None
            model.victims_lost += 1
            print(f"💀 Víctima en ({columna_aleatoria},{fila_aleatoria}) murió en el incendio")
            
            # Actualizar POIs en el escenario
            for i, poi in enumerate(model.scenario["pois"]):
                if poi[0] == fila_aleatoria and poi[1] == columna_aleatoria:
                    model.scenario["pois"].pop(i)
                    break
    
    # Caso 2: Celda con humo -> Convertir a fuego
    elif not celda["fire"] and celda["smoke"]:
        celda["fire"] = True
        celda["smoke"] = False
        if (fila_aleatoria, columna_aleatoria) not in model.scenario["fires"]:
            model.scenario["fires"].append((fila_aleatoria, columna_aleatoria))
        print(f"🔥 Fuego se propaga a ({columna_aleatoria},{fila_aleatoria}): había humo → ahora es fuego.")
        
        # Verificar si hay víctima en la celda
        if celda["poi"] == "v":
            celda["poi"] = None
            model.victims_lost += 1
            print(f"💀 Víctima en ({columna_aleatoria},{fila_aleatoria}) murió en el incendio")
            
            # Actualizar POIs en el escenario
            for i, poi in enumerate(model.scenario["pois"]):
                if poi[0] == fila_aleatoria and poi[1] == columna_aleatoria:
                    model.scenario["pois"].pop(i)
                    break
    
    # Caso 3: Celda con fuego -> EXPLOSIÓN
    elif celda["fire"]:
        print(f"💥 ¡EXPLOSIÓN! El fuego cayó en una celda que ya tenía fuego: ({columna_aleatoria},{fila_aleatoria})")
        
        # Generar explosión en las 4 direcciones: Norte, Este, Sur, Oeste
        for direccion in range(4):
            propagar_explosion(model, fila_aleatoria, columna_aleatoria, direccion)
    
    # 2. PROPAGACIÓN DE HUMO A FUEGO (segunda fase)
    nuevos_fuegos = []  # Lista de (y, x) donde habrá fuego nuevo
    nuevos_humos = []   # Lista de (y, x) donde habrá humo nuevo
    
    # Detectar propagación del fuego
    for y in range(filas):
        for x in range(columnas):
            # Si la celda tiene fuego, propagar a celdas adyacentes
            if model.grid_state[y, x]["fire"]:
                # Verificar propagación en las 4 direcciones
                for direccion in range(4):
                    # Si no hay muro en esta dirección o el muro está destruido
                    if DirectionHelper.can_pass_wall(model, y, x, direccion):
                        # Obtener coordenadas de la celda adyacente
                        nx, ny = DirectionHelper.get_adjacent_position(x, y, direccion)
                        
                        # Verificar si está dentro de los límites
                        if 0 <= ny < filas and 0 <= nx < columnas:
                            # Verificar si no está en el perímetro
                            if not DirectionHelper.is_perimeter(model, nx, ny):
                                # Verificar si la celda adyacente no tiene fuego
                                if not model.grid_state[ny, nx]["fire"]:
                                    if model.grid_state[ny, nx]["smoke"]:
                                        # Si hay humo, convertir a fuego
                                        nuevos_fuegos.append((ny, nx))
                                    else:
                                        # Si no hay humo, añadir humo
                                        nuevos_humos.append((ny, nx))
    
    # Aplicar los cambios detectados
    # Primero aplicamos los nuevos fuegos
    for y, x in nuevos_fuegos:
        model.grid_state[y, x]["fire"] = True
        model.grid_state[y, x]["smoke"] = False  # El humo se convierte en fuego
        # Añadir a la lista de fuegos del escenario
        pos_fuego = (y, x)
        if pos_fuego not in model.scenario["fires"]:
            model.scenario["fires"].append(pos_fuego)
        # Imprimir mensaje informativo
        print(f"🔥 Fuego se propaga a ({x},{y}): había humo → ahora es fuego.")
        
        # Verificar si hay víctima en la celda
        if model.grid_state[y, x]["poi"] == "v":
            model.grid_state[y, x]["poi"] = None
            model.victims_lost += 1
            print(f"💀 Víctima en ({x},{y}) murió en el incendio")
            
            # Actualizar POIs en el escenario
            for i, poi in enumerate(model.scenario["pois"]):
                if poi[0] == y and poi[1] == x:
                    model.scenario["pois"].pop(i)
                    break
    
    # Luego aplicamos los nuevos humos (evitando duplicados con los nuevos fuegos)
    for y, x in nuevos_humos:
        if (y, x) not in nuevos_fuegos:  # Evitar duplicados
            model.grid_state[y, x]["smoke"] = True
            # Imprimir mensaje informativo
            print(f"💨 Fuego genera humo en ({x},{y}).")

def propagar_explosion(model, fila, columna, direction):
    """Propaga una explosión en la dirección especificada hasta encontrar un obstáculo"""
    filas, columnas = model.grid_state.shape
    
    # Determinar la dirección del desplazamiento
    dx, dy = DirectionHelper.DIRECTIONS[direction]
    dir_name = DirectionHelper.DIRECTION_NAMES[direction]
    
    print(f"💥 ¡Explosión! El fuego se propaga al {dir_name} desde ({columna},{fila})")
    
    # Eliminar todas las puertas adyacentes al espacio objetivo de la explosión original
    if direction == DirectionHelper.NORTH:  # Solo en la primera dirección para evitar duplicados
        # Buscar puertas en las cuatro direcciones cardinales
        door_positions = compute_door_positions(model.scenario["doors"])
        
        # Verificar norte
        puerta_norte = (fila, columna, DirectionHelper.NORTH)
        if puerta_norte in door_positions:
            if puerta_norte in model.door_states:
                del model.door_states[puerta_norte]
            print(f"🚪 La explosión destruyó una puerta al norte de ({columna},{fila})")
        
        # Verificar este
        puerta_este = (fila, columna, DirectionHelper.EAST)
        if puerta_este in door_positions:
            if puerta_este in model.door_states:
                del model.door_states[puerta_este]
            print(f"🚪 La explosión destruyó una puerta al este de ({columna},{fila})")
        
        # Verificar sur
        puerta_sur = (fila, columna, DirectionHelper.SOUTH)
        if puerta_sur in door_positions:
            if puerta_sur in model.door_states:
                del model.door_states[puerta_sur]
            print(f"🚪 La explosión destruyó una puerta al sur de ({columna},{fila})")
        
        # Verificar oeste
        puerta_oeste = (fila, columna, DirectionHelper.WEST)
        if puerta_oeste in door_positions:
            if puerta_oeste in model.door_states:
                del model.door_states[puerta_oeste]
            print(f"🚪 La explosión destruyó una puerta al oeste de ({columna},{fila})")
    
    # Iniciar propagación
    x, y = columna, fila
    muro_encontrado = False
    
    while not muro_encontrado:
        # Calcular nueva posición
        nuevo_x, nuevo_y = x + dx, y + dy
        
        # Verificar si estamos dentro de los límites
        if nuevo_y < 0 or nuevo_y >= filas or nuevo_x < 0 or nuevo_x >= columnas:
            print(f"💥 Explosión detenida: alcanzó el borde del tablero en ({x},{y})")
            break
            
        # Verificar si estamos en el perímetro (donde no debe propagarse)
        if DirectionHelper.is_perimeter(model, nuevo_x, nuevo_y):
            print(f"💥 Explosión detenida: alcanzó el perímetro en ({nuevo_x},{nuevo_y})")
            break
        
        # NUEVO: Verificar primero si hay una puerta en la dirección de la explosión
        puerta_en_camino = None
        door_positions = compute_door_positions(model.scenario["doors"])
        
        puerta_en_camino = (y, x, direction)
            
        if puerta_en_camino in door_positions:
            # Hay una puerta en el camino, la eliminamos (no importa si está abierta o cerrada)
            if puerta_en_camino in model.door_states:
                del model.door_states[puerta_en_camino]
            print(f"🚪 La explosión destruyó una puerta entre ({x},{y}) y ({nuevo_x},{nuevo_y})")
            # La explosión continúa después de destruir la puerta
            y = nuevo_y
            x = nuevo_x
            continue
        
        # Verificar si hay un muro en el camino (si no hay puerta)
        hay_muro = DirectionHelper.has_wall(model, y, x, direction)
        pared_key = DirectionHelper.get_wall_key(y, x, direction)
        
        # Verificar si el muro ya tiene 2 daños (destruido)
        muro_destruido = DirectionHelper.is_wall_destroyed(model, y, x, direction)
            
        if hay_muro and not muro_destruido:
            # Agregar daño al muro
            muro_destruido = DirectionHelper.damage_wall(model, y, x, direction)
            
            print(f"🧱 Muro dañado entre ({x},{y}) y ({nuevo_x},{nuevo_y}), daño total: {model.wall_damage[pared_key]}")
            
            if muro_destruido:
                print(f"🧱 Muro entre ({x},{y}) y ({nuevo_x},{nuevo_y}) fue destruido")
                # La explosión continúa
            else:
                # Si el muro no está destruido, la explosión se detiene
                muro_encontrado = True
                break
        
        # Si el muro estaba destruido o no había muro, la explosión continúa
        if not hay_muro or muro_destruido:
            # Avanzamos a la nueva posición
            x, y = nuevo_x, nuevo_y
            celda = model.grid_state[y, x]
            
            # Si hay víctima en la celda, la víctima muere
            if celda["poi"] == "v":
                celda["poi"] = None
                model.victims_lost += 1
                print(f"💀 Víctima en ({x},{y}) murió en la explosión")
                
                # Actualizar POIs en el escenario
                for i, poi in enumerate(model.scenario["pois"]):
                    if poi[0] == y and poi[1] == x:
                        model.scenario["pois"].pop(i)
                        break
            
            # Si hay humo, se convierte en fuego
            if celda["smoke"]:
                celda["smoke"] = False
                celda["fire"] = True
                if (y, x) not in model.scenario["fires"]:
                    model.scenario["fires"].append((y, x))
                print(f"🔥 Explosión convierte humo en fuego en ({x},{y})")
            
            # Si no hay fuego ni humo, se agrega fuego
            elif not celda["fire"]:
                celda["fire"] = True
                if (y, x) not in model.scenario["fires"]:
                    model.scenario["fires"].append((y, x))
                print(f"🔥 Explosión propaga fuego a ({x},{y})")
            
            # Si ya hay fuego, la explosión continúa
            else:
                print(f"🔥 Explosión atraviesa celda con fuego en ({x},{y})")


def check_firefighters_in_fire(model):
    """Verifica si hay bomberos en celdas con fuego y los envía a la ambulancia"""
    filas, columnas = model.grid_state.shape
    bomberos_heridos = []  # Lista para rastrear bomberos heridos en este paso
    
    # Definir la posición de la ambulancia en la esquina superior derecha
    ambulance_pos = (9, 0)  # Esquina superior derecha (x=9, y=0)
    
    # Iterar por todas las celdas con fuego
    for y in range(filas):
        for x in range(columnas):
            # Si hay fuego en esta celda
            if model.grid_state[y, x]["fire"]:
                # Verificar si hay bomberos en esta celda
                cell_contents = model.grid.get_cell_list_contents((x, y))
                firefighters = [agent for agent in cell_contents if isinstance(agent, FirefighterAgent)]
                
                # Si hay bomberos en la celda con fuego
                for ff in firefighters:
                    # Agregar a la lista de heridos
                    bomberos_heridos.append(ff)
                    
    # Si no hay bomberos heridos, mostrar mensaje informativo y salir
    if not bomberos_heridos:
        print("✓ No hay bomberos en celdas con fuego")
        return
    
    # Procesar cada bombero herido
    for ff in bomberos_heridos:
        x, y = ff.pos
        print(f"🚑 ¡BOMBERO HERIDO! El bombero {ff.unique_id} está en una celda con fuego ({x},{y})")
        
        # Si el bombero lleva una víctima, la víctima se pierde
        if ff.carrying:
            ff.carrying = False
            model.victims_lost += 1
            print(f"💀 La víctima que llevaba el bombero {ff.unique_id} ha perecido en el incendio")
        
        # Enviar bombero a zona de ambulancia en la esquina superior derecha
        # Primero, quitar el bombero de su posición actual
        model.grid.remove_agent(ff)
        
        # Luego, colocarlo en la zona de ambulancia
        model.grid.place_agent(ff, ambulance_pos)
        
        print(f"🚑 El bombero {ff.unique_id} ha sido trasladado a la zona de ambulancia ({ambulance_pos})")
        
        # Reducir los AP del bombero a 0 para simular que no puede hacer más acciones este turno
        ff.ap = 0

def visualizar_simulacion(model):
    """Visualiza el estado actual de la simulación, incluyendo bomberos"""
    # Reutilizamos la visualización base de la grilla
    visualizar_grid_con_perimetro_y_puertas(
        model.scenario["grid_walls"], 
        compute_door_positions(model.scenario["doors"]), 
        model.scenario["entries"],
        model.scenario["fires"],   
        model.scenario["pois"],
        model  
    )


class FirefighterAgent(Agent):
    """Agente bombero que rescata víctimas del incendio"""
    
    def __init__(self, unique_id, model, pos):
        super().__init__(model)
        self.unique_id = unique_id
        self.ap = 4  # Puntos de acción
        self.carrying = False  # Si está cargando una víctima
        self.entrada_asignada = None  # La entrada a la que debe dirigirse
        self.direccion = None  # Dirección desde la que entra
        self.max_ap = 8  # Máximo de AP acumulables
    
    def extinguir_fuego(self, celda_y, celda_x, tipo="fuego"):
        """Intenta extinguir fuego o humo en una celda específica"""
        celda = self.model.grid_state[celda_y, celda_x]
        
        # Verificar si hay fuego o humo en la celda
        if tipo == "fuego" and celda["fire"]:
            # Verificar si hay suficiente AP para apagar fuego (2 AP)
            if self.ap >= 2:
                celda["fire"] = False
                # Eliminar de la lista de fuegos del modelo
                if (celda_y, celda_x) in self.model.scenario["fires"]:
                    self.model.scenario["fires"].remove((celda_y, celda_x))
                self.ap -= 2
                print(f"[Bombero {self.unique_id}] ACCIÓN: Apagó fuego en ({celda_x},{celda_y}). AP restante: {self.ap}")
                return True
            else:
                print(f"[Bombero {self.unique_id}] No tiene suficiente AP para apagar fuego (necesita 2 AP)")
                return False
        
        # Convertir fuego a humo (1 AP)
        elif tipo == "convertir" and celda["fire"]:
            if self.ap >= 1:
                celda["fire"] = False
                celda["smoke"] = True
                # Eliminar de la lista de fuegos del modelo
                if (celda_y, celda_x) in self.model.scenario["fires"]:
                    self.model.scenario["fires"].remove((celda_y, celda_x))
                self.ap -= 1
                print(f"[Bombero {self.unique_id}] ACCIÓN: Convirtió fuego a humo en ({celda_x},{celda_y}). AP restante: {self.ap}")
                return True
            else:
                print(f"[Bombero {self.unique_id}] No tiene suficiente AP para convertir fuego a humo (necesita 1 AP)")
                return False
        
        # Eliminar humo (1 AP)
        elif tipo == "humo" and celda["smoke"]:
            if self.ap >= 1:
                celda["smoke"] = False
                self.ap -= 1
                print(f"[Bombero {self.unique_id}] ACCIÓN: Eliminó humo en ({celda_x},{celda_y}). AP restante: {self.ap}")
                return True
            else:
                print(f"[Bombero {self.unique_id}] No tiene suficiente AP para eliminar humo (necesita 1 AP)")
                return False
        
        return False
    
    def abrir_cerrar_puerta(self, direccion):
        """Abre o cierra una puerta adyacente en la dirección especificada"""
        if self.ap < 1:
            print(f"[Bombero {self.unique_id}] No tiene suficiente AP para abrir/cerrar puerta (necesita 1 AP)")
            return False
        
        # Obtener coordenadas actuales
        x, y = self.pos
        
        # Verificar si hay una puerta en la dirección usando DirectionHelper
        if DirectionHelper.is_door(self.model, y, x, direccion):
            puerta_pos = DirectionHelper.get_wall_key(y, x, direccion)
            
            # Si existe, cambia su estado
            if puerta_pos not in self.model.door_states:
                self.model.door_states[puerta_pos] = "cerrada"  # Estado inicial cerrada
            
            # Cambia el estado
            nuevo_estado = "abierta" if self.model.door_states[puerta_pos] == "cerrada" else "cerrada"
            self.model.door_states[puerta_pos] = nuevo_estado
            
            # Restar AP
            self.ap -= 1
            
            # Usar el nombre de dirección de DirectionHelper
            nombre_direccion = DirectionHelper.DIRECTION_NAMES[direccion]
            print(f"[Bombero {self.unique_id}] ACCIÓN: {nuevo_estado.capitalize()} puerta al {nombre_direccion} desde ({x},{y}). AP restante: {self.ap}")
            return True
        else:
            print(f"[Bombero {self.unique_id}] No hay puerta al {DirectionHelper.DIRECTION_NAMES[direccion]} para abrir/cerrar")
            return False
    
    def cortar_pared(self, direccion):
        """Corta una pared adyacente en la dirección especificada"""
        if self.ap < 2:
            print(f"[Bombero {self.unique_id}] No tiene suficiente AP para cortar pared (necesita 2 AP)")
            return False
        
        # Obtener coordenadas actuales
        x, y = self.pos
        
        # Verificar si hay un muro en la dirección indicada
        if DirectionHelper.has_wall(self.model, y, x, direccion):
            # Obtener coordenadas de la celda adyacente
            nx, ny = DirectionHelper.get_adjacent_position(x, y, direccion)
            
            # Verificar si es perímetro (usando el método is_perimeter)
            es_perimetro = DirectionHelper.is_perimeter(self.model, nx, ny)
            
            if es_perimetro:
                print(f"[Bombero {self.unique_id}] ERROR: No se puede cortar una pared del perímetro exterior")
                return False
            
            # Dañar la pared usando DirectionHelper
            muro_destruido = DirectionHelper.damage_wall(self.model, y, x, direccion)
            self.ap -= 2
            
            # Mensaje según resultado y nombre de dirección de DirectionHelper
            nombre_direccion = DirectionHelper.DIRECTION_NAMES[direccion]
            if muro_destruido:
                print(f"[Bombero {self.unique_id}] ACCIÓN: Destruyó pared al {nombre_direccion} desde ({x},{y}). AP restante: {self.ap}")
            else:
                pared_key = DirectionHelper.get_wall_key(y, x, direccion)
                print(f"[Bombero {self.unique_id}] ACCIÓN: Cortó pared al {nombre_direccion} desde ({x},{y}). Pared tiene {self.model.wall_damage[pared_key]} daño. AP restante: {self.ap}")
            
            return True
        else:
            print(f"[Bombero {self.unique_id}] No hay pared al {DirectionHelper.DIRECTION_NAMES[direccion]} para cortar")
            return False
    
    def step(self):
        # Iniciar reporte de uso de AP
        print(f"\n[Bombero {self.unique_id}] Inicia turno con {self.ap} AP")
        
        # Si estamos en la fase de entrada al tablero
        if self.model.stage == 1 and self.entrada_asignada is not None:
            # Entrar al tablero en el primer paso
            self.model.grid.move_agent(self, self.entrada_asignada)
            print(f"[Bombero {self.unique_id}] ACCIÓN: Entra al tablero por la entrada {self.entrada_asignada}")
            self.entrada_asignada = None  # Ya entramos, no necesitamos recordar la entrada
            return  # Salimos porque usar la entrada consume el turno
        
        # ===== NUEVA SECCIÓN: MENÚ DE ACCIONES =====
        # Mientras tenga puntos de acción, permitir realizar acciones
        while self.ap > 0:
            # Obtener posición actual
            x, y = self.pos  # Mesa usa (x=columna, y=fila)
            celda_actual = self.model.grid_state[y, x]
            
            # VERIFICACIÓN 1: POI en celda actual (como antes)
            if celda_actual["poi"] is not None:
                if celda_actual["poi"] == "v" and not self.carrying:
                    # Es una víctima y no estamos cargando ya a otra
                    self.carrying = True
                    celda_actual["poi"] = None  # Eliminar el POI de la celda
                    print(f"[Bombero {self.unique_id}] ACCIÓN: Recogió víctima en ({x},{y})")
                elif celda_actual["poi"] == "f":
                    # Es una falsa alarma
                    celda_actual["poi"] = None  # Eliminar el POI de la celda
                    print(f"[Bombero {self.unique_id}] ACCIÓN: Encontró una falsa alarma en ({x},{y})")
            
            # VERIFICACIÓN 2: Rescate en entrada con víctima (como antes)
            if self.carrying:
                es_entrada = self.pos in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                es_perimetro = self.pos[0] == 0 or self.pos[0] == self.model.grid.width - 1 or \
                            self.pos[1] == 0 or self.pos[1] == self.model.grid.height - 1
                
                if es_entrada and es_perimetro:
                    print(f"[Bombero {self.unique_id}] ACCIÓN: ¡RESCATE COMPLETADO! Ha rescatado a la víctima en {self.pos}")
                    self.carrying = False
                    return  # El rescate consume el turno
            
            # NUEVO: DECISIÓN DE ACCIÓN (para este ejemplo, decisiones aleatorias)
            # En un juego real se permitiría al usuario elegir qué acción realizar
            acciones_posibles = []
            
            # 1. Siempre puede intentar moverse
            acciones_posibles.append("mover")
            
            # 2. Verificar si puede apagar fuego en la celda actual o adyacentes
            # Obtener celdas adyacentes
            celdas_adyacentes = []
            for direccion in range(4):
                nx, ny = DirectionHelper.get_adjacent_position(x, y, direccion)
                if 0 <= ny < self.model.grid.height and 0 <= nx < self.model.grid.width:
                    # Verificar si se puede pasar por el muro en esa dirección
                    if DirectionHelper.can_pass_wall(self.model, y, x, direccion):
                        celdas_adyacentes.append((ny, nx))

            # Verificar fuego en celda actual
            if celda_actual["fire"] and self.ap >= 2:
                acciones_posibles.append("apagar_fuego")
                acciones_posibles.append("convertir_fuego_humo")
            
            # Verificar humo en celda actual
            if celda_actual["smoke"] and self.ap >= 1:
                acciones_posibles.append("eliminar_humo")
            
            # Verificar fuego en celdas adyacentes
            for celda_y, celda_x in celdas_adyacentes:
                if self.model.grid_state[celda_y, celda_x]["fire"] and self.ap >= 2:
                    acciones_posibles.append("apagar_fuego_adyacente")
                    acciones_posibles.append("convertir_fuego_humo_adyacente")
                if self.model.grid_state[celda_y, celda_x]["smoke"] and self.ap >= 1:
                    acciones_posibles.append("eliminar_humo_adyacente")
            
            # 3. Verificar puertas adyacentes para abrir/cerrar
            muros = celda_actual["walls"]
            for i in range(4):  # Revisar en 4 direcciones
                puerta_pos = None
                if i == 0 and y > 0:  # Norte
                    puerta_pos = (y, x, 0)
                elif i == 1 and x < self.model.grid.width - 1:  # Este
                    puerta_pos = (y, x, 1)
                elif i == 2 and y < self.model.grid.height - 1:  # Sur
                    puerta_pos = (y, x, 2)
                elif i == 3 and x > 0:  # Oeste
                    puerta_pos = (y, x, 3)
                
                if puerta_pos:
                    door_positions = compute_door_positions(self.model.scenario["doors"])
                    if puerta_pos in door_positions and self.ap >= 1:
                        acciones_posibles.append(f"puerta_{i}")
            
            # 4. Verificar paredes que pueden ser cortadas
            for i in range(4):
                if muros[i] == 1 and self.ap >= 2:  # Hay un muro y tengo suficiente AP
                    # Verificación más completa del perímetro
                    es_perimetro = False
                    
                    # Verificación directa por posición de pared y dirección
                    if i == 0:  # Norte
                        if y == 1:  # La celda de arriba sería perímetro (0)
                            es_perimetro = True
                    elif i == 1:  # Este
                        if x == self.model.grid.width - 2:  # La celda a la derecha sería perímetro (width-1)
                            es_perimetro = True
                    elif i == 2:  # Sur
                        if y == self.model.grid.height - 2:  # La celda abajo sería perímetro (height-1)
                            es_perimetro = True
                    elif i == 3:  # Oeste
                        if x == 1:  # La celda a la izquierda sería perímetro (0)
                            es_perimetro = True
                            
                    # También verificar si la celda actual es perímetro y la dirección va hacia afuera
                    if (y == 0 and i == 0) or \
                    (x == self.model.grid.width - 1 and i == 1) or \
                    (y == self.model.grid.height - 1 and i == 2) or \
                    (x == 0 and i == 3):
                        es_perimetro = True
                        
                    if not es_perimetro:
                        acciones_posibles.append(f"cortar_{i}")
            
            # 5. Siempre puede pasar turno
            acciones_posibles.append("pasar")
            
            # Elegir acción aleatoriamente (para simulación)
            # En un juego real, esta elección vendría del usuario
            accion = self.model.random.choice(acciones_posibles)
            
            # Ejecutar la acción elegida
            if accion == "mover":
                # Lógica de movimiento existente
                self._realizar_movimiento()
            elif accion == "apagar_fuego":
                self.extinguir_fuego(y, x, "fuego")
            elif accion == "convertir_fuego_humo":
                self.extinguir_fuego(y, x, "convertir")
            elif accion == "eliminar_humo":
                self.extinguir_fuego(y, x, "humo")
            elif accion == "apagar_fuego_adyacente":
                # Elegir una celda adyacente con fuego al azar
                celdas_con_fuego = [(cy, cx) for cy, cx in celdas_adyacentes 
                                   if self.model.grid_state[cy, cx]["fire"]]
                if celdas_con_fuego:
                    cy, cx = self.model.random.choice(celdas_con_fuego)
                    self.extinguir_fuego(cy, cx, "fuego")
            elif accion == "convertir_fuego_humo_adyacente":
                # Elegir una celda adyacente con fuego al azar
                celdas_con_fuego = [(cy, cx) for cy, cx in celdas_adyacentes 
                                   if self.model.grid_state[cy, cx]["fire"]]
                if celdas_con_fuego:
                    cy, cx = self.model.random.choice(celdas_con_fuego)
                    self.extinguir_fuego(cy, cx, "convertir")
            elif accion == "eliminar_humo_adyacente":
                # Elegir una celda adyacente con humo al azar
                celdas_con_humo = [(cy, cx) for cy, cx in celdas_adyacentes 
                                  if self.model.grid_state[cy, cx]["smoke"]]
                if celdas_con_humo:
                    cy, cx = self.model.random.choice(celdas_con_humo)
                    self.extinguir_fuego(cy, cx, "humo")
            elif accion.startswith("puerta_"):
                direccion = int(accion.split("_")[1])
                self.abrir_cerrar_puerta(direccion)
            elif accion.startswith("cortar_"):
                direccion = int(accion.split("_")[1])
                self.cortar_pared(direccion)
            elif accion == "pasar":
                print(f"[Bombero {self.unique_id}] ACCIÓN: Pasa turno. AP restante: {self.ap}")
                # Terminar el turno
                break
        
        # Resumen del turno
        print(f"[Bombero {self.unique_id}] Finaliza turno. Posición actual: {self.pos}, Cargando víctima: {self.carrying}")
    
    def _realizar_movimiento(self):
        """Método auxiliar para realizar un movimiento, respetando las restricciones"""
        # Obtener posición actual
        x, y = self.pos
        
        # Información de depuración
        if self.carrying:
            print(f"[Debug] Bombero {self.unique_id} está cargando una víctima en ({x},{y})")
            entradas = [(e[1], e[0]) for e in self.model.scenario["entries"]]
            print(f"[Debug] Entradas disponibles: {entradas}")
        
        # Lista de movimientos posibles
        movimientos = []
        
        # Revisar las 4 direcciones
        for direccion in range(4):
            # Verificar si podemos pasar en esta dirección
            if DirectionHelper.can_pass_wall(self.model, y, x, direccion):
                # Obtener coordenadas de la celda adyacente
                nx, ny = DirectionHelper.get_adjacent_position(x, y, direccion)
                
                # Verificar si está dentro de los límites
                if 0 <= ny < self.model.grid.height and 0 <= nx < self.model.grid.width:
                    # Verificar restricciones adicionales
                    celda_destino = self.model.grid_state[ny, nx]
                    
                    # Verificar si es perímetro
                    es_perimetro = DirectionHelper.is_perimeter(self.model, nx, ny)
                    
                    # Verificar si es entrada
                    es_entrada = DirectionHelper.is_entry(self.model, nx, ny)
                    
                    # No ir a celdas con fuego si carga víctima
                    puede_ir = True
                    if self.carrying and celda_destino["fire"]:
                        puede_ir = False
                    
                    # Añadir movimiento válido
                    if puede_ir and (not es_perimetro or (self.carrying and es_entrada)):
                        movimientos.append((nx, ny))
                        if self.carrying and es_entrada:
                            print(f"[Debug] Añadido movimiento hacia entrada: {(nx, ny)}")
        
        # El resto del método permanece igual...
        # Si no hay movimientos válidos, terminar el turno
        if not movimientos:
            print(f"[Bombero {self.unique_id}] ACCIÓN: No puede moverse desde {self.pos}, AP restante: {self.ap}")
            # Información adicional de depuración cuando no puede moverse con víctima
            if self.carrying:
                print(f"[Debug] El bombero {self.unique_id} está cargando una víctima pero no puede moverse. Posibles razones:")
                print(f"  - Todas las celdas adyacentes tienen fuego")
                print(f"  - No hay entradas accesibles adyacentes")
            return False
        
        # Elegir una dirección aleatoria
        nueva_pos = self.model.random.choice(movimientos)
        
        # Verificar si es un movimiento hacia una entrada cargando víctima
        es_entrada = nueva_pos in [(e[1], e[0]) for e in self.model.scenario["entries"]]
        es_perimetro = nueva_pos[0] == 0 or nueva_pos[0] == self.model.grid.width - 1 or \
                    nueva_pos[1] == 0 or nueva_pos[1] == self.model.grid.height - 1
        
        # Mover al agente
        self.model.grid.move_agent(self, nueva_pos)
        
        # Restar punto de acción
        self.ap -= 1
        
        # Generar mensaje según el tipo de movimiento
        if self.carrying and es_entrada and es_perimetro:
            print(f"[Bombero {self.unique_id}] ACCIÓN: ¡RESCATE COMPLETADO! Salió por la entrada {nueva_pos} con la víctima. AP restante: {self.ap}")
            self.carrying = False  # Ya no carga a la víctima
            self.model.victims_rescued += 1  # NUEVO: Incrementar contador de víctimas rescatadas
            return True
        else:
            print(f"[Bombero {self.unique_id}] ACCIÓN: Se movió a {nueva_pos}. AP restante: {self.ap}")
            
            # Verificar POI en la nueva posición
            nueva_x, nueva_y = nueva_pos
            celda_nueva = self.model.grid_state[nueva_y, nueva_x]
            
            # Si hay un POI en la nueva celda
            if celda_nueva["poi"] is not None:
                if celda_nueva["poi"] == "v" and not self.carrying:
                    # Es una víctima y no estamos cargando ya a otra
                    self.carrying = True
                    celda_nueva["poi"] = None  # Eliminar el POI de la celda
                    print(f"[Bombero {self.unique_id}] ACCIÓN: Recogió víctima en ({nueva_x},{nueva_y})")
                elif celda_nueva["poi"] == "f":
                    # Es una falsa alarma
                    celda_nueva["poi"] = None  # Eliminar el POI de la celda
                    print(f"[Bombero {self.unique_id}] ACCIÓN: Encontró una falsa alarma en ({nueva_x},{nueva_y})")
            
            return True

class FireRescueModel(Model):
    """Modelo de simulación de rescate en incendio"""
    
    def __init__(self, scenario):
        super().__init__()
        
        # Configurar el espacio (ancho=10, alto=8)
        self.grid = MultiGrid(10, 8, False)  # Cambiado de SingleGrid a MultiGrid
        
        # Configurar el scheduler con activación aleatoria
        self.schedule = RandomActivation(self)
        
        # Almacenar el escenario y el estado de la grilla
        self.scenario = scenario
        self.grid_state = build_grid_state(scenario)
        
        # NUEVO: Registros para nuevas mecánicas
        self.door_states = {}  # Diccionario para estado de puertas (abiertas/cerradas)
        
        # AÑADIR: Inicializar todas las puertas como cerradas
        door_positions = compute_door_positions(scenario["doors"])
        for door_pos in door_positions:
            self.door_states[door_pos] = "cerrada"
        
        self.wall_damage = {}  # Diccionario para daño a paredes
        
        # NUEVO: Contadores para el juego
        self.victims_lost = 0      # Víctimas perdidas por el fuego
        self.victims_rescued = 0   # Víctimas rescatadas por bomberos
        self.damage_counters = 0   # Total de marcadores de daño colocados
        
        # Colocar bomberos fuera del tablero, junto a las entradas
        self.create_agents()
        
        # Contador para llevar el número de pasos
        self.step_count = 0
        
        # Etapa: 0=inicial (bomberos afuera), 1=bomberos entrando, 2+=simulación normal
        self.stage = 0
    
    def create_agents(self):
        """Crear 6 agentes bomberos distribuidos entre las entradas disponibles"""
        # Número total de bomberos que queremos crear
        num_bomberos = 6
        
        # Número de entradas disponibles
        num_entradas = len(self.scenario["entries"])
        
        for i in range(num_bomberos):
            # Seleccionar entrada cíclicamente (0, 1, 2, 3, 0, 1)
            entrada_idx = i % num_entradas
            pos = self.scenario["entries"][entrada_idx]
            
            # Determinar la dirección de la entrada y posición externa
            fila, columna = pos
            
            # Determinar qué borde está más cerca para colocar al bombero fuera
            filas, columnas = self.grid_state.shape
            dist_norte = fila
            dist_sur = filas - 1 - fila
            dist_oeste = columna
            dist_este = columnas - 1 - columna
            
            # Determinar coordenadas externas según la dirección más cercana
            if dist_norte <= min(dist_sur, dist_oeste, dist_este):
                # Entrada desde el norte, bombero arriba de la entrada
                fila_ext, col_ext = fila - 1, columna
                direccion = "norte"
            elif dist_sur <= min(dist_norte, dist_oeste, dist_este):
                # Entrada desde el sur, bombero debajo de la entrada
                fila_ext, col_ext = fila + 1, columna
                direccion = "sur"
            elif dist_oeste <= min(dist_norte, dist_sur, dist_este):
                # Entrada desde el oeste, bombero a la izquierda de la entrada
                fila_ext, col_ext = fila, columna - 1
                direccion = "oeste"
            else:
                # Entrada desde el este, bombero a la derecha de la entrada
                fila_ext, col_ext = fila, columna + 1
                direccion = "este"
            
            # Crear posición externa para Mesa (x=columna, y=fila)
            pos_mesa_ext = (col_ext, fila_ext)
            
            # Creamos el agente
            agent = FirefighterAgent(i, self, pos_mesa_ext)
            agent.entrada_asignada = (columna, fila)  # Guardamos entrada asignada
            agent.direccion = direccion  # Guardamos la dirección
            
            # IMPORTANTE: Registrar el agente en el grid para visualización
            try:
                self.grid.place_agent(agent, pos_mesa_ext)
                print(f"Bombero {i} colocado en {pos_mesa_ext}, entrará por la entrada {entrada_idx+1} ({columna},{fila})")
            except Exception as e:
                # Si falla, registrarlo en la celda más cercana válida
                print(f"No se pudo colocar bombero en {pos_mesa_ext}: {e}")
                # Usar posición de entrada como alternativa
                self.grid.place_agent(agent, (columna, fila))
                print(f"Bombero {i} colocado en la entrada {columna, fila}")
                
            self.schedule.add(agent)
    
    def step(self):
        """Avanzar la simulación un paso"""
        self.step_count += 1
        
        if self.stage == 0:
            print(f"\n--- Paso {self.step_count}: Bomberos entrando al tablero ---")
            self.stage = 1
            # Los bomberos se moverán a sus entradas en este paso
        else:
            print(f"\n--- Paso {self.step_count} ---")
            
        # Ejecutar paso de cada agente
        self.schedule.step()
        
        # Propagar el fuego después de que los agentes hayan actuado
        print("\n=== PROPAGACIÓN DEL FUEGO ===")
        advance_fire(self)
        
        # Verificar si hay bomberos en celdas con fuego
        print("\n=== VERIFICACIÓN DE BOMBEROS EN FUEGO ===")
        check_firefighters_in_fire(self)
        
        # Restaurar AP de todos los bomberos al final del turno (MODIFICADO)
        for agent in self.schedule.agents:
            # NUEVO: Acumular AP sin sobrepasar el máximo
            agent.ap = min(agent.ap + 4, agent.max_ap)  # Restaurar AP y acumular hasta max_ap
        
        # Imprimir resumen del turno
        print("\n==== Fin del turno ====")
        print(f"Víctimas rescatadas: {self.victims_rescued}")
        print(f"Víctimas perdidas: {self.victims_lost}")
        print(f"Daños acumulados en paredes: {self.damage_counters}")


# Parsear el escenario completo
scenario = parse_scenario(scenario_content)

# Calcular posiciones de puertas para visualización
door_positions = compute_door_positions(scenario["doors"])

# Mostrar mapa final con puertas
visualizar_grid_con_perimetro_y_puertas(
    scenario["grid_walls"], 
    door_positions, 
    scenario["entries"],
    scenario["fires"],   
    scenario["pois"]      
)

# Construir el estado de la grilla
print("\n=== CONSTRUYENDO ESTADO DE LA GRILLA ===")
grid_state = build_grid_state(scenario)

# Verificar que esté correctamente inicializado
verify_grid_state(grid_state)

# Información adicional
print("\nResumen del escenario y estado de grilla:")
print(f"Dimensiones del grid: {scenario['grid_walls'].shape}")
print(f"Número de POIs: {len(scenario['pois'])}")
print(f"Número de incendios iniciales: {len(scenario['fires'])}")
print(f"Número de puertas: {len(scenario['doors'])}")
print(f"Número de entradas: {len(scenario['entries'])}")


print("\n=== INICIANDO SIMULACIÓN ===")

# Inicializar el modelo con nuestro escenario
model = FireRescueModel(scenario)

# Ejecutar dos pasos de simulación para verificar funcionamiento
print("\n=== SIMULACIÓN EN PROGRESO ===")
print("\n--- Estado inicial ---")
visualizar_simulacion(model)  # Visualizar estado inicial (paso 0)

# Número de pasos a simular (cambia este valor para más o menos pasos)
num_pasos = 10

# Ejecutar la simulación para los pasos especificados
for i in range(num_pasos):
    model.step()  # Ejecutar paso
    print(f"\n--- Paso {i+1} ---")
    visualizar_simulacion(model)  # Visualizar después de cada paso

print("\n=== SIMULACIÓN FINALIZADA ===")
