using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Manages and coordinates wall and door objects by their grid coordinates.
/// Provides centralized access and state management for walls and doors throughout the simulation.
/// </summary>
public class WallDoorCoordinateManager : MonoBehaviour
{
    public static WallDoorCoordinateManager Instance;
    
    [Header("Debug Info")]
    [SerializeField] private int registeredDoors = 0;
    [SerializeField] private int registeredWalls = 0;
    
    private Dictionary<string, DoorController> doorCoordinateMap = new Dictionary<string, DoorController>();
    private Dictionary<string, WallSegment> wallCoordinateMap = new Dictionary<string, WallSegment>();
    
    /// <summary>
    /// Initializes singleton instance and registers all existing wall and door elements in the scene
    /// </summary>
    void Awake()
    {
        Instance = this;
        RegisterAllElements();
    }
    
    /// <summary>
    /// Registers all doors and walls found in the scene for coordinate-based lookup
    /// </summary>
    private void RegisterAllElements()
    {
        RegisterDoorsFromScene();
        RegisterWallsFromScene();
    }
    
    /// <summary>
    /// Finds and registers all DoorController objects in the scene by their coordinate positions
    /// </summary>
    private void RegisterDoorsFromScene()
    {
        DoorController[] doors = FindObjectsByType<DoorController>(FindObjectsSortMode.None);
        
        foreach (var door in doors)
        {
            string coordinateKey = GetCoordinateKey(door.cellA_coords, door.cellB_coords);
            doorCoordinateMap[coordinateKey] = door;
        }
        
        registeredDoors = doorCoordinateMap.Count;
    }
    
    /// <summary>
    /// Finds and registers all WallSegment objects in the scene by their coordinate positions
    /// </summary>
    private void RegisterWallsFromScene()
    {
        WallSegment[] walls = FindObjectsByType<WallSegment>(FindObjectsSortMode.None);
        
        foreach (var wall in walls)
        {
            string coordinateKey = GetCoordinateKey(wall.cellA_coords, wall.cellB_coords);
            wallCoordinateMap[coordinateKey] = wall;
        }
        
        registeredWalls = wallCoordinateMap.Count;
    }
    
    /// <summary>
    /// Updates a door's state based on its coordinate position with extensive debugging information
    /// </summary>
   public void UpdateDoorByCoordinates(Vector2Int fromCell, Vector2Int toCell, string newState)
{
    string coordsString = $"({fromCell.x},{fromCell.y})-({toCell.x},{toCell.y})";
    string key1 = GetCoordinateKey(fromCell, toCell);
    string key2 = GetCoordinateKey(toCell, fromCell);
    
    Debug.Log($"[DOOR DEBUG] Buscando puerta en: {coordsString}");
    Debug.Log($"[DOOR DEBUG] Claves generadas: '{key1}' y '{key2}'");
    
    DoorController door = GetDoorByCoordinates(fromCell, toCell);
    
    if (door != null)
    {
        Debug.Log($"[DOOR FOUND] Puerta encontrada: {door.name}");
        Debug.Log($"[DOOR FOUND] Coords en puerta: ({door.cellA_coords.x},{door.cellA_coords.y})-({door.cellB_coords.x},{door.cellB_coords.y})");
        
        string previousState = "unknown";
        if (door.GetType().GetProperty("currentState") != null)
        {
            previousState = door.GetType().GetProperty("currentState").GetValue(door, null) as string;
        }
        
        door.SetDoorState(newState);
        
        if (door.IsEntry())
        {
            Debug.Log($"[DOOR ENTRY] La puerta de entrada entre {coordsString} ignora cambios de estado - siempre abierta");
        }
        else
        {
            Debug.Log($"[DOOR UPDATE] Estado actualizado: {coordsString} -> {previousState} a {newState}");
        }
    }
    else
    {
        Debug.LogWarning($"[DOOR MISSING] ¡PUERTA NO ENCONTRADA entre {coordsString}!");
        
        Debug.LogWarning("[DOOR REGISTRY] Puertas registradas en el diccionario:");
        foreach (var k in doorCoordinateMap.Keys)
        {
            DoorController d = doorCoordinateMap[k];
            string type = d.IsEntry() ? "ENTRY" : "regular";
            Debug.Log($"  - Clave: {k} -> {d.name} [{type}]");
        }
        
        DoorController[] allDoors = FindObjectsByType<DoorController>(FindObjectsSortMode.None);
        Debug.LogWarning($"[DOOR SCENE] {allDoors.Length} puertas encontradas en la escena:");
        
        foreach (var d in allDoors)
        {
            string doorKey = GetCoordinateKey(d.cellA_coords, d.cellB_coords);
            string type = d.IsEntry() ? "ENTRY" : "regular";
            bool isRegistered = doorCoordinateMap.ContainsKey(doorKey);
            
            Debug.Log($"  - {d.name} [{type}]: ({d.cellA_coords.x},{d.cellA_coords.y})-({d.cellB_coords.x},{d.cellB_coords.y})");
            Debug.Log($"    Clave: {doorKey}, Registrada: {isRegistered}");
        }
    }
}

    /// <summary>
    /// Updates wall damage level based on coordinate position
    /// </summary>
    public void UpdateWallDamageByCoordinates(Vector2Int fromCell, Vector2Int toCell, int damageLevel)
    {
        WallSegment wall = GetWallByCoordinates(fromCell, toCell);
        if (wall != null)
        {
            wall.SetDamage(damageLevel);
            Debug.Log($"Updated wall damage: ({fromCell.x},{fromCell.y}) to ({toCell.x},{toCell.y}) -> damage level {damageLevel}");
        }
        else
        {
            Debug.LogWarning($"Wall not found between coordinates ({fromCell.x},{fromCell.y}) and ({toCell.x},{toCell.y})");
        }
    }
    
    /// <summary>
    /// Retrieves a door controller by its coordinate endpoints, checking both forward and reverse order
    /// </summary>
    public DoorController GetDoorByCoordinates(Vector2Int fromCell, Vector2Int toCell)
    {
        string key1 = GetCoordinateKey(fromCell, toCell);
        string key2 = GetCoordinateKey(toCell, fromCell);
        
        if (doorCoordinateMap.ContainsKey(key1))
            return doorCoordinateMap[key1];
        else if (doorCoordinateMap.ContainsKey(key2))
            return doorCoordinateMap[key2];
            
        return null;
    }
    
    /// <summary>
    /// Retrieves a wall segment by its coordinate endpoints, checking both forward and reverse order
    /// </summary>
    public WallSegment GetWallByCoordinates(Vector2Int fromCell, Vector2Int toCell)
    {
        string key1 = GetCoordinateKey(fromCell, toCell);
        string key2 = GetCoordinateKey(toCell, fromCell);
        
        if (wallCoordinateMap.ContainsKey(key1))
            return wallCoordinateMap[key1];
        else if (wallCoordinateMap.ContainsKey(key2))
            return wallCoordinateMap[key2];
            
        return null;
    }
    
    /// <summary>
    /// Creates a consistent coordinate key string by ordering coordinates consistently
    /// </summary>
    private string GetCoordinateKey(Vector2Int fromCell, Vector2Int toCell)
    {
        Vector2Int minCell = new Vector2Int(Mathf.Min(fromCell.x, toCell.x), Mathf.Min(fromCell.y, toCell.y));
        Vector2Int maxCell = new Vector2Int(Mathf.Max(fromCell.x, toCell.x), Mathf.Max(fromCell.y, toCell.y));
        return $"({minCell.x},{minCell.y})-({maxCell.x},{maxCell.y})";
    }
    
    /// <summary>
    /// Gets the count of registered doors in the system
    /// </summary>
    public int GetRegisteredDoorCount() => registeredDoors;
    
    /// <summary>
    /// Gets the count of registered walls in the system
    /// </summary>
    public int GetRegisteredWallCount() => registeredWalls;
    
    /// <summary>
    /// Returns a list of all registered door controllers
    /// </summary>
    public List<DoorController> GetAllRegisteredDoors() => new List<DoorController>(doorCoordinateMap.Values);
    
    /// <summary>
    /// Returns a list of all registered wall segments
    /// </summary>
    public List<WallSegment> GetAllRegisteredWalls() => new List<WallSegment>(wallCoordinateMap.Values);
    
    /// <summary>
    /// Filters and returns only entry doors from all registered doors
    /// </summary>
    public List<DoorController> GetEntryDoors()
    {
        List<DoorController> entryDoors = new List<DoorController>();
        foreach (var door in doorCoordinateMap.Values)
        {
            if (door.IsEntry())
                entryDoors.Add(door);
        }
        return entryDoors;
    }
    
    /// <summary>
    /// Filters and returns only regular (non-entry) doors from all registered doors
    /// </summary>
    public List<DoorController> GetRegularDoors()
    {
        List<DoorController> regularDoors = new List<DoorController>();
        foreach (var door in doorCoordinateMap.Values)
        {
            if (!door.IsEntry())
                regularDoors.Add(door);
        }
        return regularDoors;
    }
    
    /// <summary>
    /// Clears and re-registers all wall and door elements from the scene
    /// </summary>
    [ContextMenu("Refresh Wall and Door Registration")]
    public void RefreshRegistration()
    {
        doorCoordinateMap.Clear();
        wallCoordinateMap.Clear();
        RegisterAllElements();
    }
}