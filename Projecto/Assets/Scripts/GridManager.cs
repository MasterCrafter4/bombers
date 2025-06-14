using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Manages the grid system by registering and providing access to all Cell3D objects in the scene.
/// Acts as a centralized registry for quick cell lookup by coordinates.
/// </summary>
public class GridManager : MonoBehaviour
{
    public static GridManager Instance;
    private Dictionary<Vector2Int, Cell3D> gridMap = new Dictionary<Vector2Int, Cell3D>();

    /// <summary>
    /// Initializes the singleton instance and registers all existing Cell3D objects in the scene
    /// </summary>
    private void Awake()
    {
        Instance = this;

        Cell3D[] cells = FindObjectsByType<Cell3D>(FindObjectsSortMode.None);

        foreach (var cell in cells)
        {
            Vector2Int pos = new Vector2Int(cell.x, cell.y);

            if (!gridMap.ContainsKey(pos))
            {
                gridMap[pos] = cell;
            }
            else
            {
                Debug.LogWarning($"Duplicate cell at position {pos}");
            }
        }
        
        Debug.Log($"GridManager registered {gridMap.Count} cells");
    }

    /// <summary>
    /// Registers a Cell3D object at its coordinate position in the grid map
    /// </summary>
    public void RegisterCell(Cell3D cell)
    {
        Vector2Int pos = new Vector2Int(cell.x, cell.y);
        if (!gridMap.ContainsKey(pos))
            gridMap[pos] = cell;
    }

    /// <summary>
    /// Retrieves a Cell3D object at the specified grid coordinates
    /// </summary>
    public Cell3D GetCell(int x, int y)
    {
        Vector2Int pos = new Vector2Int(x, y);
        return gridMap.ContainsKey(pos) ? gridMap[pos] : null;
    }
}