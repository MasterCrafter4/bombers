
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import SingleGrid  # Usamos SingleGrid en lugar de MultiGrid
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Contenido del escenario (formato completo)
scenario_content = """1001 1000 1000 1000 1100 0001 1000 1100
0001 0000 0110 0011 0010 0010 0010 0100
0000 0000 1001 1000 1000 1100 1001 0100
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
            # Verificar si hay fuego en esta celda
            is_fire = (y, x) in fires if fires else False
            
            # Determinar el color de fondo según la celda
            if is_fire:
                color = '#ffcccc'  # Color rojizo claro para fuego
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
                
                if entrada_e:
                    # Dibujar entrada este
                    ax.plot([x+1, x+1], [filas - y - 0.75, filas - y - 0.25], color='white', linewidth=4.0)
                elif puerta_e:
                    # Dibujar puerta este
                    puerta_color = 'brown'
                    if model is not None and (y, x, 1) in model.door_states:
                        puerta_abierta = model.door_states[(y, x, 1)] == "abierta"
                        puerta_color = 'green' if puerta_abierta else 'brown'
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
                
                if entrada_s:
                    # Dibujar entrada sur
                    ax.plot([x+0.25, x+0.75], [filas - y - 1, filas - y - 1], color='white', linewidth=4.0)
                elif puerta_s:
                    # Dibujar puerta sur
                    puerta_color = 'brown'
                    if model is not None and (y, x, 2) in model.door_states:
                        puerta_abierta = model.door_states[(y, x, 2)] == "abierta"
                        puerta_color = 'green' if puerta_abierta else 'brown'
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
                    # Dibujar puerta oeste
                    puerta_color = 'brown'
                    if model is not None and (y, x, 3) in model.door_states:
                        puerta_abierta = model.door_states[(y, x, 3)] == "abierta"
                        puerta_color = 'green' if puerta_abierta else 'brown'
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
                
                if entrada_e:
                    # Dibujar entrada este
                    ax.plot([x+1, x+1], [filas - y - 0.75, filas - y - 0.25], color='white', linewidth=4.0)
                elif puerta_e:
                    # Dibujar puerta este
                    ax.plot([x+1, x+1], [filas - y - 0.75, filas - y - 0.25], color='brown', linewidth=2.5)
                elif muro_e:
                    # Dibujar muro este
                    ax.plot([x+1, x+1], [filas - y - 1, filas - y], color='black', linewidth=2.5)
                
                if entrada_s:
                    # Dibujar entrada sur
                    ax.plot([x+0.25, x+0.75], [filas - y - 1, filas - y - 1], color='white', linewidth=4.0)
                elif puerta_s:
                    # Dibujar puerta sur
                    ax.plot([x+0.25, x+0.75], [filas - y - 1, filas - y - 1], color='brown', linewidth=2.5)
                elif muro_s:
                    # Dibujar muro sur
                    ax.plot([x, x+1], [filas - y - 1, filas - y - 1], color='black', linewidth=2.5)
                
                if entrada_o:
                    # Dibujar entrada oeste
                    ax.plot([x, x], [filas - y - 0.75, filas - y - 0.25], color='white', linewidth=4.0)
                elif puerta_o:
                    # Dibujar puerta oeste
                    ax.plot([x, x], [filas - y - 0.75, filas - y - 0.25], color='brown', linewidth=2.5)
                elif muro_o:
                    # Dibujar muro oeste
                    ax.plot([x, x], [filas - y - 1, filas - y], color='black', linewidth=2.5)
                    
    # Agregar elementos a la leyenda
    entrada_line = plt.Line2D([0], [0], color='white', linewidth=4.0, label='Entrada bomberos')
    perimetro_patch = patches.Patch(color='#b3e6b3', label='Perímetro')
    jugable_patch = patches.Patch(color='#e6f7ff', label='Celda jugable')
    puerta_line = plt.Line2D([0], [0], color='brown', linewidth=2.5, label='Puerta')
    muro_line = plt.Line2D([0], [0], color='black', linewidth=2.5, label='Muro')
    
    # Nuevos elementos para la leyenda
    fire_marker = plt.Line2D([0], [0], marker='o', markersize=15, markerfacecolor='#ff6600', 
                             markeredgecolor='red', alpha=0.7, linestyle='', label='Fuego')
    victim_marker = plt.Line2D([0], [0], marker='D', markersize=12, markerfacecolor='#00cc66', 
                             markeredgecolor='black', linestyle='', label='Víctima (POI)')
    false_alarm_marker = plt.Line2D([0], [0], marker='X', markersize=12, markerfacecolor='#cccccc', 
                             markeredgecolor='black', linestyle='', label='Falsa alarma (POI)')
    
    ax.legend(handles=[perimetro_patch, jugable_patch, entrada_line, muro_line, puerta_line, 
                      fire_marker, victim_marker, false_alarm_marker], 
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

<<<<<<< Updated upstream
# Agregar después de la función visualizar_grid_con_perimetro_y_puertas y antes de la definición de clases
=======
def advance_fire(model):
    """Propaga el fuego a través del escenario"""
    filas, columnas = model.grid_state.shape
    
    # Registrar los cambios a realizar (para evitar propagar fuego recién creado en este turno)
    nuevos_fuegos = []  # Lista de (y, x) donde habrá fuego nuevo
    nuevos_humos = []   # Lista de (y, x) donde habrá humo nuevo
    
    # Paso 1: Detectar propagación del fuego
    for y in range(filas):
        for x in range(columnas):
            # Si la celda tiene fuego, propagar a celdas adyacentes
            if model.grid_state[y, x]["fire"]:
                # Obtener los muros de la celda actual
                muros = model.grid_state[y, x]["walls"]
                
                # Verificar propgación hacia el Norte (y-1)
                if y > 0 and not muros[0]:  # Si no hay muro al norte
                    # Verificar si la celda norte tiene muro hacia el sur
                    if not model.grid_state[y-1, x]["walls"][2]:
                        # Verificar si la celda norte no tiene fuego
                        if not model.grid_state[y-1, x]["fire"]:
                            # NUEVO: Verificar que no estamos en el perímetro
                            es_perimetro = (y-1 == 0 or x == 0 or x == columnas-1 or y-1 == filas-1)
                            if not es_perimetro:
                                if model.grid_state[y-1, x]["smoke"]:
                                    # Si hay humo, convertir a fuego
                                    nuevos_fuegos.append((y-1, x))
                                else:
                                    # Si no hay humo, añadir humo
                                    nuevos_humos.append((y-1, x))
                
                # Verificar propgación hacia el Este (x+1)
                if x < columnas-1 and not muros[1]:  # Si no hay muro al este
                    # Verificar si la celda este tiene muro hacia el oeste
                    if not model.grid_state[y, x+1]["walls"][3]:
                        # Verificar si la celda este no tiene fuego
                        if not model.grid_state[y, x+1]["fire"]:
                            # NUEVO: Verificar que no estamos en el perímetro
                            es_perimetro = (y == 0 or x+1 == columnas-1 or x+1 == 0 or y == filas-1)
                            if not es_perimetro:
                                if model.grid_state[y, x+1]["smoke"]:
                                    # Si hay humo, convertir a fuego
                                    nuevos_fuegos.append((y, x+1))
                                else:
                                    # Si no hay humo, añadir humo
                                    nuevos_humos.append((y, x+1))
                
                # Verificar propgación hacia el Sur (y+1)
                if y < filas-1 and not muros[2]:  # Si no hay muro al sur
                    # Verificar si la celda sur tiene muro hacia el norte
                    if not model.grid_state[y+1, x]["walls"][0]:
                        # Verificar si la celda sur no tiene fuego
                        if not model.grid_state[y+1, x]["fire"]:
                            # NUEVO: Verificar que no estamos en el perímetro
                            es_perimetro = (y+1 == 0 or x == 0 or x == columnas-1 or y+1 == filas-1)
                            if not es_perimetro:
                                if model.grid_state[y+1, x]["smoke"]:
                                    # Si hay humo, convertir a fuego
                                    nuevos_fuegos.append((y+1, x))
                                else:
                                    # Si no hay humo, añadir humo
                                    nuevos_humos.append((y+1, x))
                
                # Verificar propgación hacia el Oeste (x-1)
                if x > 0 and not muros[3]:  # Si no hay muro al oeste
                    # Verificar si la celda oeste tiene muro hacia el este
                    if not model.grid_state[y, x-1]["walls"][1]:
                        # Verificar si la celda oeste no tiene fuego
                        if not model.grid_state[y, x-1]["fire"]:
                            # NUEVO: Verificar que no estamos en el perímetro
                            es_perimetro = (y == 0 or x-1 == columnas-1 or x-1 == 0 or y == filas-1)
                            if not es_perimetro:
                                if model.grid_state[y, x-1]["smoke"]:
                                    # Si hay humo, convertir a fuego
                                    nuevos_fuegos.append((y, x-1))
                                else:
                                    # Si no hay humo, añadir humo
                                    nuevos_humos.append((y, x-1))
    
    # Paso 2: Aplicar los cambios detectados
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
    
    # Luego aplicamos los nuevos humos (evitando duplicados con los nuevos fuegos)
    for y, x in nuevos_humos:
        if (y, x) not in nuevos_fuegos:  # Evitar duplicados
            model.grid_state[y, x]["smoke"] = True
            # Imprimir mensaje informativo
            print(f"💨 Fuego genera humo en ({x},{y}).")
>>>>>>> Stashed changes

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
        """Abre o cierra una puerta adyacente en la dirección especificada (N=0, E=1, S=2, O=3)"""
        if self.ap < 1:
            print(f"[Bombero {self.unique_id}] No tiene suficiente AP para abrir/cerrar puerta (necesita 1 AP)")
            return False
        
        # Obtener coordenadas actuales
        x, y = self.pos
        
        # Buscar si hay una puerta en la dirección especificada
        puerta_pos = None
        
        # Revisar si hay puerta en la dirección indicada
        if direccion == 0:  # Norte
            puerta_pos = (y, x, 0)
        elif direccion == 1:  # Este
            puerta_pos = (y, x, 1)
        elif direccion == 2:  # Sur
            puerta_pos = (y, x, 2)
        elif direccion == 3:  # Oeste
            puerta_pos = (y, x, 3)
        
        # Verificar si la puerta existe en las puertas del escenario
        door_positions = compute_door_positions(self.model.scenario["doors"])
        if puerta_pos in door_positions:
            # Si existe, cambia su estado
            if puerta_pos not in self.model.door_states:
                self.model.door_states[puerta_pos] = "cerrada"  # Estado inicial cerrada
            
            # Cambia el estado
            nuevo_estado = "abierta" if self.model.door_states[puerta_pos] == "cerrada" else "cerrada"
            self.model.door_states[puerta_pos] = nuevo_estado
            
            # Restar AP
            self.ap -= 1
            
            # Texto para la dirección
            direcciones = ["norte", "este", "sur", "oeste"]
            print(f"[Bombero {self.unique_id}] ACCIÓN: {nuevo_estado.capitalize()} puerta al {direcciones[direccion]} desde ({x},{y}). AP restante: {self.ap}")
            return True
        else:
            print(f"[Bombero {self.unique_id}] No hay puerta al {['norte', 'este', 'sur', 'oeste'][direccion]} para abrir/cerrar")
            return False
    
    def cortar_pared(self, direccion):
        """Corta una pared adyacente en la dirección especificada (N=0, E=1, S=2, O=3)"""
        if self.ap < 2:
            print(f"[Bombero {self.unique_id}] No tiene suficiente AP para cortar pared (necesita 2 AP)")
            return False
        
        # Obtener coordenadas actuales
        x, y = self.pos
        
        # Verificar si hay un muro en la dirección indicada
        muros = self.model.grid_state[y, x]["walls"]
        
        # Verificar pared de perímetro - Este es el cambio clave
        es_perimetro = False
        
        # Verificación directa por posición de pared y dirección
        if direccion == 0:  # Norte
            if y == 1:  # La celda de arriba sería perímetro (0)
                es_perimetro = True
        elif direccion == 1:  # Este
            if x == self.model.grid.width - 2:  # La celda a la derecha sería perímetro (width-1)
                es_perimetro = True
        elif direccion == 2:  # Sur
            if y == self.model.grid.height - 2:  # La celda abajo sería perímetro (height-1)
                es_perimetro = True
        elif direccion == 3:  # Oeste
            if x == 1:  # La celda a la izquierda sería perímetro (0)
                es_perimetro = True
        
        # También verificar si la celda actual es perímetro y la dirección va hacia afuera
        if (y == 0 and direccion == 0) or \
        (x == self.model.grid.width - 1 and direccion == 1) or \
        (y == self.model.grid.height - 1 and direccion == 2) or \
        (x == 0 and direccion == 3):
            es_perimetro = True
            
        if muros[direccion] == 1:  # Hay un muro en esa dirección
            if es_perimetro:
                print(f"[Bombero {self.unique_id}] ERROR: No se puede cortar una pared del perímetro exterior")
                return False
            
            # Crear clave para el muro
            pared_key = (y, x, direccion)
            
            # Añadir daño a la pared
            if pared_key not in self.model.wall_damage:
                self.model.wall_damage[pared_key] = 1
            else:
                self.model.wall_damage[pared_key] += 1
            
            # Restar AP
            self.ap -= 2
            
            # Determinar si la pared está destruida
            if self.model.wall_damage[pared_key] >= 2:
                # Destruir la pared (eliminar muro)
                self.model.grid_state[y, x]["walls"][direccion] = 0
                
                # También eliminar el muro correspondiente desde la otra celda
                if direccion == 0 and y > 0:  # Norte
                    self.model.grid_state[y-1, x]["walls"][2] = 0  # Sur de la celda norte
                elif direccion == 1 and x < self.model.grid.width - 1:  # Este
                    self.model.grid_state[y, x+1]["walls"][3] = 0  # Oeste de la celda este
                elif direccion == 2 and y < self.model.grid.height - 1:  # Sur
                    self.model.grid_state[y+1, x]["walls"][0] = 0  # Norte de la celda sur
                elif direccion == 3 and x > 0:  # Oeste
                    self.model.grid_state[y, x-1]["walls"][1] = 0  # Este de la celda oeste
                
                print(f"[Bombero {self.unique_id}] ACCIÓN: Destruyó pared al {['norte', 'este', 'sur', 'oeste'][direccion]} desde ({x},{y}). AP restante: {self.ap}")
            else:
                print(f"[Bombero {self.unique_id}] ACCIÓN: Cortó pared al {['norte', 'este', 'sur', 'oeste'][direccion]} desde ({x},{y}). Pared tiene {self.model.wall_damage[pared_key]} daño. AP restante: {self.ap}")
            
            return True
        else:
            print(f"[Bombero {self.unique_id}] No hay pared al {['norte', 'este', 'sur', 'oeste'][direccion]} para cortar")
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
            celdas_adyacentes = []
            # Obtener coordenadas de celdas adyacentes
            if y > 0:  # Norte
                celdas_adyacentes.append((y - 1, x))
            if x < self.model.grid.width - 1:  # Este
                celdas_adyacentes.append((y, x + 1))
            if y < self.model.grid.height - 1:  # Sur
                celdas_adyacentes.append((y + 1, x))
            if x > 0:  # Oeste
                celdas_adyacentes.append((y, x - 1))
            
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
        
        # Obtener celda actual y sus muros [N, E, S, O]
        celda_actual = self.model.grid_state[y, x]
        muros = celda_actual["walls"]
        
        # Posibles movimientos (N, E, S, O) y sus coordenadas relativas
        movimientos = []
        
        # Debugging: mostrar más información cuando está cargando una víctima
        if self.carrying:
            print(f"[Debug] Bombero {self.unique_id} está cargando una víctima en ({x},{y})")
            # Mostrar entradas disponibles
            entradas = [(e[1], e[0]) for e in self.model.scenario["entries"]]
            print(f"[Debug] Entradas disponibles: {entradas}")
        
        # Norte (y-1)
        if y > 0:  # No estamos en el borde superior
            pos_norte = (x, y - 1)
            # Verificar si podemos pasar (no hay muro o está destruido)
            puede_pasar = not muros[0]
            # También revisar si el muro está destruido
            pared_key = (y, x, 0)
            if pared_key in self.model.wall_damage and self.model.wall_damage[pared_key] >= 2:
                puede_pasar = True
            
            if puede_pasar and self.model.grid.is_cell_empty(pos_norte):
                # Verificar restricciones adicionales
                celda_destino = self.model.grid_state[y - 1, x]
                
                # Verificar si es perímetro
                es_perimetro = pos_norte[0] == 0 or pos_norte[0] == self.model.grid.width - 1 or \
                            pos_norte[1] == 0 or pos_norte[1] == self.model.grid.height - 1
                
                # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                es_entrada = pos_norte in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                
                # NUEVA RESTRICCIÓN corregida: No ir a celdas con fuego si carga víctima
                puede_ir = True
                if self.carrying and celda_destino["fire"]:
                    puede_ir = False
                    
                if puede_ir:
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_norte)
                        if self.carrying and es_entrada:
                            print(f"[Debug] Añadido movimiento hacia entrada: {pos_norte}")
        
        # Este (x+1)
        if x < self.model.grid.width - 1:  # No estamos en el borde derecho
            pos_este = (x + 1, y)
            # Verificar si podemos pasar (no hay muro o está destruido)
            puede_pasar = not muros[1]
            # También revisar si el muro está destruido
            pared_key = (y, x, 1)
            if pared_key in self.model.wall_damage and self.model.wall_damage[pared_key] >= 2:
                puede_pasar = True
            
            if puede_pasar and self.model.grid.is_cell_empty(pos_este):
                # Verificar restricciones adicionales
                celda_destino = self.model.grid_state[y, x + 1]
                
                # Verificar si es perímetro
                es_perimetro = pos_este[0] == 0 or pos_este[0] == self.model.grid.width - 1 or \
                            pos_este[1] == 0 or pos_este[1] == self.model.grid.height - 1
                
                # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                es_entrada = pos_este in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                
                # NUEVA RESTRICCIÓN corregida: No ir a celdas con fuego si carga víctima
                puede_ir = True
                if self.carrying and celda_destino["fire"]:
                    puede_ir = False
                    
                if puede_ir:
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_este)
                        if self.carrying and es_entrada:
                            print(f"[Debug] Añadido movimiento hacia entrada: {pos_este}")
        
        # Sur (y+1)
        if y < self.model.grid.height - 1:  # No estamos en el borde inferior
            pos_sur = (x, y + 1)
            # Verificar si podemos pasar (no hay muro o está destruido)
            puede_pasar = not muros[2]
            # También revisar si el muro está destruido
            pared_key = (y, x, 2)
            if pared_key in self.model.wall_damage and self.model.wall_damage[pared_key] >= 2:
                puede_pasar = True
            
            if puede_pasar and self.model.grid.is_cell_empty(pos_sur):
                # Verificar restricciones adicionales
                celda_destino = self.model.grid_state[y + 1, x]
                
                # Verificar si es perímetro
                es_perimetro = pos_sur[0] == 0 or pos_sur[0] == self.model.grid.width - 1 or \
                            pos_sur[1] == 0 or pos_sur[1] == self.model.grid.height - 1
                
                # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                es_entrada = pos_sur in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                
                # NUEVA RESTRICCIÓN corregida: No ir a celdas con fuego si carga víctima
                puede_ir = True
                if self.carrying and celda_destino["fire"]:
                    puede_ir = False
                    
                if puede_ir:
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_sur)
                        if self.carrying and es_entrada:
                            print(f"[Debug] Añadido movimiento hacia entrada: {pos_sur}")
        
        # Oeste (x-1)
        if x > 0:  # No estamos en el borde izquierdo
            pos_oeste = (x - 1, y)
            # Verificar si podemos pasar (no hay muro o está destruido)
            puede_pasar = not muros[3]
            # También revisar si el muro está destruido
            pared_key = (y, x, 3)
            if pared_key in self.model.wall_damage and self.model.wall_damage[pared_key] >= 2:
                puede_pasar = True
            
            if puede_pasar and self.model.grid.is_cell_empty(pos_oeste):
                # Verificar restricciones adicionales
                celda_destino = self.model.grid_state[y, x - 1]
                
                # Verificar si es perímetro
                es_perimetro = pos_oeste[0] == 0 or pos_oeste[0] == self.model.grid.width - 1 or \
                            pos_oeste[1] == 0 or pos_oeste[1] == self.model.grid.height - 1
                
                # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                es_entrada = pos_oeste in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                
                # NUEVA RESTRICCIÓN corregida: No ir a celdas con fuego si carga víctima
                puede_ir = True
                if self.carrying and celda_destino["fire"]:
                    puede_ir = False
                    
                if puede_ir:
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_oeste)
                        if self.carrying and es_entrada:
                            print(f"[Debug] Añadido movimiento hacia entrada: {pos_oeste}")
        
        # Si no hay movimientos válidos, terminar el turno
        if not movimientos:
            print(f"[Bombero {self.unique_id}] ACCIÓN: No puede moverse desde {self.pos}, AP restante: {self.ap}")
            # Información adicional de depuración cuando no puede moverse con víctima
            if self.carrying:
                print(f"[Debug] El bombero {self.unique_id} está cargando una víctima pero no puede moverse. Posibles razones:")
                print(f"  - Todas las celdas adyacentes tienen fuego")
                print(f"  - Todas las celdas adyacentes están ocupadas")
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
        self.grid = SingleGrid(10, 8, False)  # SingleGrid en lugar de MultiGrid
        
        # Configurar el scheduler con activación aleatoria
        self.schedule = RandomActivation(self)
        
        # Almacenar el escenario y el estado de la grilla
        self.scenario = scenario
        self.grid_state = build_grid_state(scenario)
        
        # NUEVO: Registros para nuevas mecánicas
        self.door_states = {}  # Diccionario para estado de puertas (abiertas/cerradas)
        self.wall_damage = {}  # Diccionario para daño a paredes
        
        # Colocar bomberos fuera del tablero, junto a las entradas
        self.create_agents()
        
        # Contador para llevar el número de pasos
        self.step_count = 0
        
        # Etapa: 0=inicial (bomberos afuera), 1=bomberos entrando, 2+=simulación normal
        self.stage = 0
    
    def create_agents(self):
        """Crear los agentes bomberos en posiciones fuera del tablero, junto a las entradas"""
        for i, pos in enumerate(self.scenario["entries"]):
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
                self.grid.place_agent(agent, pos_mesa_ext)  # Añadir esta línea
                print(f"Bombero {i} colocado en {pos_mesa_ext}")
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
        
<<<<<<< Updated upstream
        # Restaurar AP de todos los bomberos al final del turno
=======
        # Propagar el fuego después de que los agentes hayan actuado
        print("\n=== PROPAGACIÓN DEL FUEGO ===")
        advance_fire(self)
        
        # Restaurar AP de todos los bomberos al final del turno (MODIFICADO)
>>>>>>> Stashed changes
        for agent in self.schedule.agents:
            # NUEVO: Acumular AP sin sobrepasar el máximo
            agent.ap = min(agent.ap + 4, agent.max_ap)  # Restaurar AP y acumular hasta max_ap
        
        # Imprimir resumen del turno
        print("\n==== Fin del turno ====")


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
