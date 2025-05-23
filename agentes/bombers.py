import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Contenido del escenario (6x8)
scenario_content = """1001 1000 1000 1000 1100 0001 1000 1100
0001 0000 0110 0011 0010 0010 0010 0100
0000 0000 1001 1000 1000 1100 1001 0100
0011 0110 0011 0000 0010 0010 0010 0010
1001 1000 1000 0000 1100 1001 1100 1101
0011 0010 0000 0010 0010 0010 0010 0110"""

# Paso 1: Parsear el contenido a matriz (6, 8, 4)
original_grid = np.zeros((6, 8, 4), dtype=int)
for i, line in enumerate(scenario_content.strip().split('\n')):
    for j, cell in enumerate(line.strip().split()):
        original_grid[i, j] = [int(d) for d in cell]

# Paso 2: Crear grid extendido con perímetro (8, 10, 4)
grid = np.zeros((8, 10, 4), dtype=int)

# Copiar escenario original en centro (1:7, 1:9)
grid[1:7, 1:9] = original_grid

# Agregar muros en el perímetro externo
grid[0, 1:9, 0] = 1  # Norte
grid[7, 1:9, 2] = 1  # Sur
grid[1:7, 0, 3] = 1  # Oeste
grid[1:7, 9, 1] = 1  # Este

# 4. Puertas (siempre comienzan cerradas): 
#    cada tupla ((r1,c1),(r2,c2)) une dos celdas adyacentes
doors = [
    ((1,3),(1,4)),
    ((2,5),(2,6)),
    ((2,8),(3,8)),
    ((3,2),(3,3)),
    ((4,4),(5,4)),
    ((4,6),(4,7)),
    ((6,5),(6,6)),
    ((6,7),(6,8)),
]

entries = [
    (1,6),
    (3,1),
    (4,8),
    (6,3),
]


# Función para marcar puertas en grid (convertimos coordenadas a índices de la grid con perímetro)
door_positions = []
for (r1, c1), (r2, c2) in doors:
    # Ajustar índices para el grid con perímetro
    r1_adj, c1_adj = r1, c1
    r2_adj, c2_adj = r2, c2
    
    # Determinar en qué dirección está la puerta
    if r1 == r2:  # Puerta horizontal (este-oeste)
        if c1 < c2:  # c1 está a la izquierda de c2
            door_positions.append((r1_adj, c1_adj, 1))  # Puerta en el este de celda 1
        else:
            door_positions.append((r1_adj, c2_adj, 1))  # Puerta en el este de celda 2
    else:  # Puerta vertical (norte-sur)
        if r1 < r2:  # r1 está arriba de r2
            door_positions.append((r1_adj, c1_adj, 2))  # Puerta en el sur de celda 1
        else:
            door_positions.append((r2_adj, c2_adj, 2))  # Puerta en el sur de celda 2

# Función de visualización con cuadrícula + muros + perímetro + puertas
def visualizar_grid_con_perimetro_y_puertas(grid, door_positions, entries):
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
            # Fondo: solo perímetro o jugable
            if x == 0 or x == columnas-1 or y == 0 or y == filas-1:
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
                    
    # Agregar leyenda
    entrada_line = plt.Line2D([0], [0], color='white', linewidth=4.0, label='Entrada bomberos')
    perimetro_patch = patches.Patch(color='#b3e6b3', label='Perímetro')
    jugable_patch = patches.Patch(color='#e6f7ff', label='Celda jugable')
    puerta_line = plt.Line2D([0], [0], color='brown', linewidth=2.5, label='Puerta')
    muro_line = plt.Line2D([0], [0], color='black', linewidth=2.5, label='Muro')
    
    ax.legend(handles=[perimetro_patch, jugable_patch, entrada_line, muro_line, puerta_line], 
              loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=5)

    # Aspecto visual
    ax.set_xticks(range(columnas))
    ax.set_yticks(range(filas))
    ax.set_xticklabels(range(columnas))
    ax.set_yticklabels(range(filas - 1, -1, -1))
    ax.set_aspect('equal')
    ax.set_xlim(0, columnas)
    ax.set_ylim(0, filas)
    ax.set_title("Mapa del Escenario 6×8 con Perímetro (8×10), Muros y Puertas")
    ax.grid(False)
    plt.tight_layout()
    plt.show()

# Mostrar mapa final con puertas
visualizar_grid_con_perimetro_y_puertas(grid, door_positions, entries)