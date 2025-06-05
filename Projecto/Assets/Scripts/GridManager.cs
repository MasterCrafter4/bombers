using UnityEngine;
using System.Collections.Generic;


public class GridManager : MonoBehaviour
{
    public static GridManager Instance;
    private Dictionary<Vector2Int, Cell3D> gridMap = new Dictionary<Vector2Int, Cell3D>();

    void Awake()
    {
        Instance = this;
    }

    public void RegisterCell(Cell3D cell)
    {
        Vector2Int pos = new Vector2Int(cell.x, cell.y);
        if (!gridMap.ContainsKey(pos))
            gridMap[pos] = cell;
    }

    public Cell3D GetCell(int x, int y)
    {
        Vector2Int pos = new Vector2Int(x, y);
        return gridMap.ContainsKey(pos) ? gridMap[pos] : null;
    }
}
