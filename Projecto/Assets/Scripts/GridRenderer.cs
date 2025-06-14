using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Renders and manages the visual grid by updating existing Cell3D objects with server data.
/// Provides coordinate conversion utilities for translating between grid and world positions.
/// </summary>
public class GridRenderer : MonoBehaviour
{
    public static GridRenderer Instance;
    private Dictionary<Vector2Int, Cell3D> gridMap = new();

    /// <summary>
    /// Initializes the singleton instance and maps all existing Cell3D objects in the scene
    /// </summary>
    private void Awake()
    {
        Instance = this;

        Cell3D[] cells = FindObjectsByType<Cell3D>(FindObjectsSortMode.None);

        foreach (var cell in cells)
        {
            Vector2Int pos = new Vector2Int(cell.x, cell.y);

            if (!gridMap.ContainsKey(pos))
                gridMap[pos] = cell;
            else
                Debug.LogWarning($"Celda duplicada en posición {pos}");
        }
    }

    /// <summary>
    /// Updates existing cells with data from the server grid without creating new instances
    /// </summary>
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

    /// <summary>
    /// Converts logical grid coordinates to world position
    /// </summary>
    public Vector3 GetCellWorldPosition(int x, int y)
    {
        return new Vector3(x, 0.5f, y);
    }

    /// <summary>
    /// Retrieves a specific cell by its grid coordinates
    /// </summary>
    public Cell3D GetCell(int x, int y)
    {
        Vector2Int pos = new Vector2Int(x, y);
        return gridMap.ContainsKey(pos) ? gridMap[pos] : null;
    }
}