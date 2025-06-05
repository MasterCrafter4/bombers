using UnityEngine;
using System.Collections.Generic;

public class GridRenderer : MonoBehaviour
{
    public static GridRenderer Instance;
    private Dictionary<Vector2Int, Cell3D> gridMap = new();

    private void Awake()
    {
        Instance = this;

        // Buscar todas las celdas con Cell3D ya colocadas en la escena
        Cell3D[] cells = FindObjectsOfType<Cell3D>();

        foreach (var cell in cells)
        {
            Vector2Int pos = new Vector2Int(cell.x, cell.y);

            if (!gridMap.ContainsKey(pos))
                gridMap[pos] = cell;
            else
                Debug.LogWarning($"Celda duplicada en posición {pos}");
        }
    }

    // Este método ya no instancia, solo actualiza las celdas con los datos del JSON
    public void BuildGrid(Grid grid)
    {
        foreach (var cell in grid.cells)
        {
            Vector2Int pos = new Vector2Int(cell.x, cell.y);

            if (gridMap.TryGetValue(pos, out Cell3D cell3D))
            {
                cell3D.SetData(cell);
            }
            else
            {
                Debug.LogWarning($"No se encontró una celda en la posición {pos}");
            }
        }
    }

    // Convertir coordenadas lógicas a posición en mundo, por si lo necesitas
    public Vector3 GetCellWorldPosition(int x, int y)
    {
        return new Vector3(x, 0.5f, y);
    }

    // Obtener una celda específica por coordenadas
    public Cell3D GetCell(int x, int y)
    {
        Vector2Int pos = new Vector2Int(x, y);
        return gridMap.ContainsKey(pos) ? gridMap[pos] : null;
    }
}
