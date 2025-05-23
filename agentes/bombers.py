
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
                # Dibujar muros (bien posicionados)
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
                    # Dibujar puerta norte
                    ax.plot([x+0.25, x+0.75], [filas - y, filas - y], color='brown', linewidth=2.5)
                elif muro_n:
                    # Dibujar muro norte
                    ax.plot([x, x+1], [filas - y, filas - y], color='black', linewidth=2.5)
                
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
    # Dibujar símbolos para humo si corresponde
    if model is not None:
        for y in range(filas):
            for x in range(columnas):
                if model.grid_state[y, x]["smoke"]:
                    ax.plot(x + 0.5, filas - y - 0.5, 's', markersize=15, 
                            markerfacecolor='gray', markeredgecolor='darkgray', alpha=0.5)

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
    smoke_marker = plt.Line2D([0], [0], marker='s', markersize=15, markerfacecolor='gray', 
                           markeredgecolor='darkgray', alpha=0.5, linestyle='', label='Humo')
    
    # Ajustar límites de visualización para no expandir tanto
    if model is not None:
        # Límites más ajustados para ver mejor el tablero
        ax.set_xlim(-0.5, columnas+0.5) 
        ax.set_ylim(-0.5, filas+0.5)
    
    # Definir bombero_marker aquí, antes de usarlo
    bombero_marker = plt.Line2D([0], [0], marker='o', markersize=15, 
                               markerfacecolor='blue', markeredgecolor='navy', 
                               alpha=0.7, linestyle='', label='Bombero')

    # Definir la leyenda correctamente según si hay modelo o no
    if model is not None:
        # Leyenda con bomberos
        ax.legend(handles=[perimetro_patch, jugable_patch, entrada_line, muro_line, 
                         puerta_line, fire_marker, victim_marker, false_alarm_marker,
                         bombero_marker, smoke_marker], 
                 loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
        
        # Configurar límites para ver TODA el área, incluido el exterior
        ax.set_xlim(-1, columnas+1) 
        ax.set_ylim(-1, filas+1)
        
        # Dibujar bomberos
        for agent in model.schedule.agents:
            x, y = agent.pos  # Mesa usa (x=columna, y=fila)
            # Dibujamos bomberos con coordenadas ajustadas
            ax.plot(x + 0.5, filas - y - 0.5, 'o', markersize=24, 
                   markerfacecolor='blue', markeredgecolor='navy', alpha=0.7, zorder=25)
            ax.text(x + 0.5, filas - y - 0.5, str(agent.unique_id), color='white', 
                   fontsize=12, ha='center', va='center', zorder=26)
    else:
        # Leyenda sin bomberos
        ax.legend(handles=[perimetro_patch, jugable_patch, entrada_line, muro_line, puerta_line, 
                         fire_marker, victim_marker, false_alarm_marker, smoke_marker], 
                 loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
    
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

class FirefighterAgent (Agent):
    """Agente bombero que rescata víctimas del incendio"""
    
    def __init__(self, unique_id, model, pos):
        super().__init__(model)
        self.unique_id = unique_id
        self.ap = 4  # Puntos de acción
        self.carrying = False  # Si está cargando una víctima
        self.entrada_asignada = None  # La entrada a la que debe dirigirse
        self.direccion = None  # Dirección desde la que entra
    
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
        
        # Mientras tenga puntos de acción, moverse aleatoriamente
        while self.ap > 0:
            # Obtener posición actual
            x, y = self.pos  # Mesa usa (x=columna, y=fila)
            
            # Obtener celda actual y sus muros [N, E, S, O]
            celda_actual = self.model.grid_state[y, x]
            muros = celda_actual["walls"]
            
            # Posibles movimientos (N, E, S, O) y sus coordenadas relativas
            movimientos = []
            
            # Norte (y-1)
            if not muros[0] and y > 0:  # No hay muro al norte y no estamos en el borde
                pos_norte = (x, y - 1)
                # Verificar si la celda está vacía
                if self.model.grid.is_cell_empty(pos_norte):
                    # Verificar si estamos saliendo del área jugable (entrando al perímetro)
                    es_perimetro = pos_norte[0] == 0 or pos_norte[0] == self.model.grid.width - 1 or \
                                  pos_norte[1] == 0 or pos_norte[1] == self.model.grid.height - 1
                    
                    # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                    es_entrada = pos_norte in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                    
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_norte)
            
            # Este (x+1)
            if not muros[1] and x < self.model.grid.width - 1:  # No hay muro al este y no estamos en el borde
                pos_este = (x + 1, y)
                # Verificar si la celda está vacía
                if self.model.grid.is_cell_empty(pos_este):
                    # Verificar si estamos saliendo del área jugable
                    es_perimetro = pos_este[0] == 0 or pos_este[0] == self.model.grid.width - 1 or \
                                  pos_este[1] == 0 or pos_este[1] == self.model.grid.height - 1
                    
                    # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                    es_entrada = pos_este in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                    
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_este)
            
            # Sur (y+1)
            if not muros[2] and y < self.model.grid.height - 1:  # No hay muro al sur y no estamos en el borde
                pos_sur = (x, y + 1)
                # Verificar si la celda está vacía
                if self.model.grid.is_cell_empty(pos_sur):
                    # Verificar si estamos saliendo del área jugable
                    es_perimetro = pos_sur[0] == 0 or pos_sur[0] == self.model.grid.width - 1 or \
                                  pos_sur[1] == 0 or pos_sur[1] == self.model.grid.height - 1
                    
                    # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                    es_entrada = pos_sur in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                    
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_sur)
            
            # Oeste (x-1)
            if not muros[3] and x > 0:  # No hay muro al oeste y no estamos en el borde
                pos_oeste = (x - 1, y)
                # Verificar si la celda está vacía
                if self.model.grid.is_cell_empty(pos_oeste):
                    # Verificar si estamos saliendo del área jugable
                    es_perimetro = pos_oeste[0] == 0 or pos_oeste[0] == self.model.grid.width - 1 or \
                                  pos_oeste[1] == 0 or pos_oeste[1] == self.model.grid.height - 1
                    
                    # Solo permitir salir si estoy cargando una víctima y la celda es una entrada
                    es_entrada = pos_oeste in [(e[1], e[0]) for e in self.model.scenario["entries"]]
                    
                    if not es_perimetro or (self.carrying and es_entrada):
                        movimientos.append(pos_oeste)
            
            # Si no hay movimientos válidos, terminar el turno
            if not movimientos:
                print(f"[Bombero {self.unique_id}] ACCIÓN: No puede moverse desde {self.pos}, AP restante: {self.ap}")
                break
            
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
            else:
                print(f"[Bombero {self.unique_id}] ACCIÓN: Se movió a {nueva_pos}. AP restante: {self.ap}")
        
        # Resumen del turno
        print(f"[Bombero {self.unique_id}] Finaliza turno. Posición actual: {self.pos}, Cargando víctima: {self.carrying}")

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
        
        # Propagar el fuego después de que los agentes hayan actuado
        print("\n=== PROPAGACIÓN DEL FUEGO ===")
        advance_fire(self)
        
        # Restaurar AP de todos los bomberos al final del turno
        for agent in self.schedule.agents:
            agent.ap = 4  # Restaurar a 4 AP
        
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

model.step()  # Paso 1 (bomberos entrando)
print("\n--- Paso 1: Bomberos entrando al tablero ---")
visualizar_simulacion(model)  # Visualizar después del paso 1

model.step()  # Paso 2 (bomberos ya dentro)
print("\n--- Paso 2: Bomberos dentro del tablero ---")
visualizar_simulacion(model)  # Visualizar después del paso 2

print("\n=== SIMULACIÓN FINALIZADA ===")