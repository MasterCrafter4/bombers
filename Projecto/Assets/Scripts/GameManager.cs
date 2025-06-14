using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Central coordinator that manages the entire fire rescue simulation.
/// Processes server responses and distributes updates to appropriate subsystem managers.
/// </summary>
public class GameManager : MonoBehaviour
{
    [Header("Debug")]
    public bool enableDebugMode = true;

    [Header("Manager References")]
    public FirefighterManager firefighterManager;

    /// <summary>
    /// Initializes manager references and subscribes to server events
    /// </summary>
    void Start()
    {
        if (firefighterManager == null)
        {
            firefighterManager = FindFirstObjectByType<FirefighterManager>();
        }

        ServerClient.OnStepReceived += HandleStepReceived;
    }

    /// <summary>
    /// Unsubscribes from events when object is destroyed
    /// </summary>
    void OnDestroy()
    {
        ServerClient.OnStepReceived -= HandleStepReceived;
    }

    /// <summary>
    /// Main handler for server response processing and frame distribution
    /// </summary>
    private void HandleStepReceived(StepR stepResponse)
    {
        Debug.Log("Datos recibidos del servidor. Procesando visualización...");

        if (stepResponse.frames != null && stepResponse.frames.Count > 0)
        {
            foreach (var frame in stepResponse.frames)
            {
                ProcessFrame(frame);
            }
        }
    }

    /// <summary>
    /// Processes individual frames based on their action type
    /// </summary>
    private void ProcessFrame(GameState frame)
    {
        string actionType = frame.action?.type ?? "unknown";

        Debug.Log($"Procesando frame: {frame.frame}, turno: {frame.turn}, tipo: {actionType}");

        switch (actionType)
        {
            case "initial_state":
                ProcessInitialState(frame);
                break;
            case "end_of_turn":
                ProcessEndOfTurn(frame);
                break;
            default:
                ProcessRegularAction(frame);
                break;
        }

        ProcessFirefighters(frame.firefighters);
    }

    /// <summary>
    /// Handles initial game state setup including grid and firefighter spawning
    /// </summary>
    private void ProcessInitialState(GameState frame)
    {
        if (frame.grid != null)
        {
            GridRenderer.Instance.BuildGrid(frame.grid);
            Debug.Log("Estado inicial: cuadrícula actualizada");
        }

        if (frame.firefighters != null && frame.firefighters.Count > 0)
        {
            if (firefighterManager != null)
            {
                firefighterManager.SpawnAll(frame.firefighters);
                Debug.Log($"Estado inicial: {frame.firefighters.Count} bomberos generados");
            }
            else
            {
                Debug.LogError("FirefighterManager no encontrado!");
            }
        }
    }

    /// <summary>
    /// Processes end of turn updates including fire propagation and POI validation
    /// </summary>
    private void ProcessEndOfTurn(GameState frame)
    {
        if (frame.grid_changes != null && frame.grid_changes.Count > 0)
        {
            Debug.Log($"Fin de turno: actualizando {frame.grid_changes.Count} celdas modificadas");
            foreach (var gridChange in frame.grid_changes)
            {
                UpdateCellFromGridChange(gridChange);
            }
        }
        else if (frame.grid != null)
        {
            GridRenderer.Instance.BuildGrid(frame.grid);
            Debug.Log("Fin de turno: cuadrícula completa actualizada");
        }
        
        if (POIManager.Instance != null)
        {
            POIManager.Instance.CleanupNullPOIs();
            int totalPOIs = POIManager.Instance.GetTotalActivePOIsCount();
            if (totalPOIs < 3)
            {
                Debug.LogWarning($"Fin de turno: Solo {totalPOIs} POIs activos (incluyendo transportados)");
            }
        }
    }

    /// <summary>
    /// Processes regular gameplay actions including door interactions and wall damage
    /// </summary>
    private void ProcessRegularAction(GameState frame)
    {
        string actionType = frame.action?.type ?? "unknown";

        if (frame.grid_changes != null && frame.grid_changes.Count > 0)
        {
            Debug.Log($"Acción: actualizando {frame.grid_changes.Count} celdas modificadas");
            foreach (var gridChange in frame.grid_changes)
            {
                UpdateCellFromGridChange(gridChange);
            }
        }
        
        if (frame.pois != null)
        {
            ProcessPOIs(frame.pois);
        }

        if (frame.wall_damage != null && frame.wall_damage.Count > 0)
        {
            Debug.Log($"Procesando daño a {frame.wall_damage.Count} muros");
            foreach (var wallDamage in frame.wall_damage)
            {
                ProcessWallDamage(wallDamage);
            }
        }

        if (actionType == "open_close_door" && frame.action.firefighter_id != 0 && firefighterManager != null)
        {
            int firefighterId = frame.action.firefighter_id;

            if (frame.doors != null && frame.doors.Count > 0)
            {
                Door doorChange = frame.doors[0];
                Vector2Int fromCell = new Vector2Int(doorChange.from[0], doorChange.from[1]);
                Vector2Int toCell = new Vector2Int(doorChange.to[0], doorChange.to[1]);

                firefighterManager.ProcessDoorAction(firefighterId, fromCell, toCell, () =>
                {
                    ProcessDoorChange(doorChange);
                });
            }
        }
        else if (actionType == "cut_wall" && frame.action.firefighter_id != 0 && firefighterManager != null)
        {
            int firefighterId = frame.action.firefighter_id;

            if (frame.wall_damage != null && frame.wall_damage.Count > 0)
            {
                var wallDamage = frame.wall_damage[0];
                Vector3 wallPosition = GetMidpoint(
                    new Vector2Int(wallDamage.from[0], wallDamage.from[1]),
                    new Vector2Int(wallDamage.to[0], wallDamage.to[1])
                );

                if (firefighterManager.TryGetFirefighter(firefighterId, out FirefighterController controller))
                {
                    Vector3 lookDirection = wallPosition - controller.transform.position;
                    if (lookDirection != Vector3.zero)
                    {
                        controller.transform.rotation = Quaternion.LookRotation(lookDirection);
                    }
                }
            }
        }
        else if (frame.doors != null && frame.doors.Count > 0)
        {
            foreach (var doorChange in frame.doors)
            {
                ProcessDoorChange(doorChange);
            }
        }
    }

    /// <summary>
    /// Updates all firefighter positions and states from server data
    /// </summary>
    private void ProcessFirefighters(List<Firefighter> firefighters)
    {
        if (firefighters != null && firefighters.Count > 0 && firefighterManager != null)
        {
            firefighterManager.UpdateFirefighters(firefighters);
        }
    }

    /// <summary>
    /// Updates a single cell with new data from the server
    /// </summary>
    private void UpdateCell(Cell cellData)
    {
        Cell3D cell3D = GridManager.Instance.GetCell(cellData.x, cellData.y);

        if (cell3D != null)
        {
            cell3D.SetData(cellData);

            if (enableDebugMode)
            {
                string status = "";
                if (cellData.fire) status += "FUEGO ";
                if (cellData.smoke) status += "HUMO ";
                if (!string.IsNullOrEmpty(cellData.poi)) status += $"POI({cellData.poi}) ";
                if (status == "") status = "normal";
                Debug.Log($"Celda ({cellData.x},{cellData.y}) actualizada: {status}");
            }
        }
        else
        {
            Debug.LogWarning($"No se encontró celda 3D para actualizar en ({cellData.x},{cellData.y})");
        }
    }

    /// <summary>
    /// Processes door state changes from server updates
    /// </summary>
    private void ProcessDoorChange(Door doorState)
    {
        Vector2Int fromCell = new Vector2Int(doorState.from[0], doorState.from[1]);
        Vector2Int toCell = new Vector2Int(doorState.to[0], doorState.to[1]);
        string newState = doorState.state.ToLower();

        Debug.Log($"Cambio de puerta: ({fromCell.x},{fromCell.y})->({toCell.x},{toCell.y}) -> {newState}");

        WallDoorCoordinateManager doorManager = WallDoorCoordinateManager.Instance;
        if (doorManager != null)
        {
            doorManager.UpdateDoorByCoordinates(fromCell, toCell, newState);
        }
        else
        {
            Debug.LogError("WallDoorCoordinateManager no encontrado!");
        }
    }

    /// <summary>
    /// Processes wall damage updates from server data
    /// </summary>
    private void ProcessWallDamage(WallDamage damage)
    {
        Vector2Int fromCell = new Vector2Int(damage.from[0], damage.from[1]);
        Vector2Int toCell = new Vector2Int(damage.to[0], damage.to[1]);

        Debug.Log($"Daño a muro: ({fromCell.x},{fromCell.y})->({toCell.x},{toCell.y}) -> nivel {damage.damage}");

        WallDoorCoordinateManager wallManager = WallDoorCoordinateManager.Instance;
        if (wallManager != null)
        {
            wallManager.UpdateWallDamageByCoordinates(fromCell, toCell, damage.damage);
        }
        else
        {
            Debug.LogError("WallDoorCoordinateManager no encontrado!");
        }
    }

    /// <summary>
    /// Updates cells from grid changes while preserving POIs when appropriate
    /// </summary>
    private void UpdateCellFromGridChange(GridChange gridChange)
    {
        Cell3D cell3D = GridManager.Instance.GetCell(gridChange.x, gridChange.y);

        if (cell3D != null)
        {
            if (gridChange.fire)
            {
                cell3D.SetFire(true);
                cell3D.SetSmoke(false);
                cell3D.SetPOI(null);
            }
            else if (gridChange.smoke && gridChange.poi == null)
            {
                string currentPOI = cell3D.GetPOIType();
                
                cell3D.SetFire(false);
                cell3D.SetSmoke(true);
                
                Debug.Log($"Preservando POI existente '{currentPOI}' en celda ({gridChange.x},{gridChange.y}) con humo");
            }
            else
            {
                cell3D.SetFire(gridChange.fire);
                cell3D.SetSmoke(gridChange.smoke);
                cell3D.SetPOI(gridChange.poi);
            }

            if (enableDebugMode)
            {
                string status = "";
                if (gridChange.fire) status += "FUEGO ";
                if (gridChange.smoke) status += "HUMO ";
                if (!string.IsNullOrEmpty(gridChange.poi)) status += $"POI({gridChange.poi}) ";
                if (status == "") status = "normal";
                Debug.Log($"Celda ({gridChange.x},{gridChange.y}) actualizada: {status}");
            }
        }
        else
        {
            Debug.LogWarning($"No se encontró celda 3D para actualizar en ({gridChange.x},{gridChange.y})");
        }
    }

    /// <summary>
    /// Calculates midpoint between two grid coordinates in world space
    /// </summary>
    private Vector3 GetMidpoint(Vector2Int from, Vector2Int to)
    {
        Vector3 fromPos = firefighterManager.GetWorldPositionPublic(from.x, from.y);
        Vector3 toPos = firefighterManager.GetWorldPositionPublic(to.x, to.y);
        return (fromPos + toPos) * 0.5f;
    }
    
    /// <summary>
    /// Processes Points of Interest updates from server data
    /// </summary>
    private void ProcessPOIs(List<Poi> pois) 
    {
        if (pois == null || pois.Count == 0)
            return;
            
        Debug.Log($"Procesando {pois.Count} POIs recibidos del servidor");
        
        foreach (var poi in pois)
        {
            Cell3D cell = GridManager.Instance.GetCell(poi.x, poi.y);
            if (cell != null)
            {
                cell.SetPOI(poi.type);
                Debug.Log($"POI tipo '{poi.type}' colocado en ({poi.x},{poi.y})");
            }
        }
    }
}