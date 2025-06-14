using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Manages all firefighters in the simulation including spawning, updating positions, and handling actions.
/// Coordinates firefighter behavior and provides central access to firefighter controllers.
/// </summary>
public class FirefighterManager : MonoBehaviour
{
    [Header("Prefab Configuration")]
    public GameObject firefighterPrefab;

    [Header("Visual Settings")]
    public float moveSpeed = 2f;
    public float heightOffset = 0.5f;

    [Header("Debug")]
    public bool showDebugInfo = true;

    public static FirefighterManager Instance { get; private set; }

    private Dictionary<int, FirefighterController> spawnedFirefighters = new Dictionary<int, FirefighterController>();

    /// <summary>
    /// Initializes the singleton instance
    /// </summary>
    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
        }
    }

    /// <summary>
    /// Spawn all firefighters for the initial state
    /// </summary>
    public void SpawnAll(List<Firefighter> firefighters)
    {
        ClearAllFirefighters();

        if (firefighters == null)
        {
            Debug.LogWarning("No firefighter data provided");
            return;
        }

        foreach (var ff in firefighters)
        {
            SpawnFirefighter(ff);
        }

        if (showDebugInfo)
        {
            Debug.Log($"FirefighterManager: Spawned {firefighters.Count} firefighters");
        }
    }

    /// <summary>
    /// Update a specific firefighter's position and stats
    /// </summary>
    public void UpdateFirefighter(Firefighter firefighterData)
    {
        if (firefighterData == null) return;

        if (spawnedFirefighters.TryGetValue(firefighterData.id, out FirefighterController controller))
        {
            Cell3D cell = GridManager.Instance.GetCell(firefighterData.x, firefighterData.y);
            Vector2Int cellPos = new Vector2Int(firefighterData.x, firefighterData.y);

            if (cell != null)
            {
                if (!controller.carrying && firefighterData.carrying)
                {
                    if (POIManager.Instance != null)
                    {
                        POIManager.Instance.RemovePOI(cellPos);
                        POIManager.Instance.ValidateAndCleanPOIs();
                    }
                    cell.SetPOI(null);
                    Debug.Log($"Bombero {firefighterData.id} recogió víctima en ({firefighterData.x},{firefighterData.y})");
                }
                else if (cell.GetPOIType() == "f")
                {
                    if (POIManager.Instance != null)
                    {
                        POIManager.Instance.RemovePOI(cellPos);
                        POIManager.Instance.ValidateAndCleanPOIs();
                    }
                    cell.SetPOI(null);
                    Debug.Log($"Bombero {firefighterData.id} descubrió POI falso en ({firefighterData.x},{firefighterData.y})");
                }
            }

            Vector3 targetPosition = GetWorldPosition(firefighterData.x, firefighterData.y);
            controller.MoveTo(targetPosition, moveSpeed);
            controller.UpdateAP(firefighterData.ap);
            controller.SetCarrying(firefighterData.carrying);

            if (showDebugInfo)
            {
                Debug.Log($"Bombero {firefighterData.id} actualizado: pos({firefighterData.x},{firefighterData.y}), AP:{firefighterData.ap}, llevando:{firefighterData.carrying}");
            }
        }
        else
        {
            Debug.LogWarning($"Bombero con ID {firefighterData.id} no encontrado - creando uno nuevo");
            SpawnFirefighter(firefighterData);
        }
    }

    /// <summary>
    /// Update multiple firefighters at once
    /// </summary>
    public void UpdateFirefighters(List<Firefighter> firefighters)
    {
        if (firefighters == null) return;

        foreach (var ff in firefighters)
        {
            UpdateFirefighter(ff);
        }
    }

    /// <summary>
    /// Attempts to get a firefighter controller by ID
    /// </summary>
    public bool TryGetFirefighter(int firefighterId, out FirefighterController controller)
    {
        return spawnedFirefighters.TryGetValue(firefighterId, out controller);
    }

    /// <summary>
    /// Spawn a single firefighter
    /// </summary>
    private void SpawnFirefighter(Firefighter firefighterData)
    {
        if (firefighterPrefab == null)
        {
            Debug.LogError("FirefighterManager: Firefighter prefab not assigned!");
            return;
        }

        Vector3 spawnPosition = GetWorldPosition(firefighterData.x, firefighterData.y);

        GameObject ffObj = Instantiate(firefighterPrefab, spawnPosition, Quaternion.identity);
        FirefighterController controller = ffObj.GetComponent<FirefighterController>();

        if (controller == null)
        {
            controller = ffObj.AddComponent<FirefighterController>();
        }

        controller.Initialize(firefighterData.id, firefighterData.ap, firefighterData.carrying);
        ffObj.name = $"Firefighter_{firefighterData.id}";

        spawnedFirefighters[firefighterData.id] = controller;

        if (showDebugInfo)
        {
            Debug.Log($"Spawned Firefighter {firefighterData.id} at ({firefighterData.x},{firefighterData.y}) with {firefighterData.ap} AP");
        }
    }

    /// <summary>
    /// Convert grid coordinates to world position
    /// </summary>
    private Vector3 GetWorldPosition(int x, int y)
    {
        if (GridRenderer.Instance != null)
        {
            Vector3 position = GridRenderer.Instance.GetCellWorldPosition(x, y);

            position = new Vector3(-position.x * 2.0f, position.y, position.z * 2.0f);

            Vector3 centerOffset = new Vector3(4f, 0, -4f);
            position += centerOffset;

            if (showDebugInfo)
            {
                Debug.Log($"GridRenderer path: grid({x},{y}) -> raw({GridRenderer.Instance.GetCellWorldPosition(x, y)}) -> final({position})");
            }

            return position + Vector3.up * heightOffset;
        }

        float scale = 2.0f;

        return new Vector3(-y * scale, heightOffset, x * scale);
    }

    /// <summary>
    /// Get firefighter controller by ID
    /// </summary>
    public FirefighterController GetFirefighterById(int id)
    {
        spawnedFirefighters.TryGetValue(id, out FirefighterController controller);
        return controller;
    }

    /// <summary>
    /// Clear all spawned firefighters
    /// </summary>
    public void ClearAllFirefighters()
    {
        foreach (var controller in spawnedFirefighters.Values)
        {
            if (controller != null && controller.gameObject != null)
            {
                Destroy(controller.gameObject);
            }
        }
        spawnedFirefighters.Clear();

        if (showDebugInfo)
        {
            Debug.Log("FirefighterManager: Cleared all firefighters");
        }
    }

    /// <summary>
    /// Processes fire extinguishing action for a specific firefighter
    /// </summary>
    public void ProcessFireExtinguishAction(int firefighterId, int targetX, int targetY, bool isSmoke, System.Action onCompleted = null)
    {
        if (!spawnedFirefighters.TryGetValue(firefighterId, out FirefighterController controller))
        {
            Debug.LogWarning($"No se encontró bombero con ID {firefighterId}");
            onCompleted?.Invoke();
            return;
        }

        Vector3 targetPosition = GetWorldPosition(targetX, targetY);

        if (!controller.IsAdjacentTo(targetPosition))
        {
            Debug.LogWarning($"Bombero {firefighterId} no está adyacente a la celda ({targetX},{targetY}) para extinguir");
            onCompleted?.Invoke();
            return;
        }

        controller.ExtinguishFire(targetPosition, onCompleted);

        if (showDebugInfo)
        {
            Debug.Log($"Bombero {firefighterId} extinguiendo {(isSmoke ? "humo" : "fuego")} en ({targetX},{targetY})");
        }
    }

    /// <summary>
    /// Get count of active firefighters
    /// </summary>
    public int GetFirefighterCount()
    {
        return spawnedFirefighters.Count;
    }

    /// <summary>
    /// Draws debug gizmos for firefighter positions
    /// </summary>
    void OnDrawGizmos()
    {
        if (Application.isPlaying && showDebugInfo)
        {
            foreach (var ff in spawnedFirefighters)
            {
                Gizmos.color = Color.yellow;
                Gizmos.DrawWireCube(ff.Value.transform.position, Vector3.one * 0.3f);
            }
        }
    }

    /// <summary>
    /// Processes door interaction action for a specific firefighter
    /// </summary>
    public void ProcessDoorAction(int firefighterId, Vector2Int doorFrom, Vector2Int doorTo, System.Action onCompleted = null)
    {
        if (!spawnedFirefighters.TryGetValue(firefighterId, out FirefighterController controller))
        {
            Debug.LogWarning($"No se encontró bombero con ID {firefighterId}");
            onCompleted?.Invoke();
            return;
        }

        Vector3 doorPosition = GetWorldPosition((doorFrom.x + doorTo.x) / 2, (doorFrom.y + doorTo.y) / 2);

        if (!controller.IsAdjacentTo(doorPosition))
        {
            Debug.LogWarning($"Bombero {firefighterId} no está cerca de la puerta en ({doorFrom.x},{doorFrom.y})-({doorTo.x},{doorTo.y})");
            onCompleted?.Invoke();
            return;
        }

        Vector3 lookDirection = doorPosition - controller.transform.position;
        if (lookDirection != Vector3.zero)
        {
            controller.transform.rotation = Quaternion.LookRotation(lookDirection);
        }

        StartCoroutine(DelayedDoorAction(0.2f, onCompleted));

        if (showDebugInfo)
        {
            Debug.Log($"Bombero {firefighterId} interactuando con puerta en ({doorFrom.x},{doorFrom.y})-({doorTo.x},{doorTo.y})");
        }
    }

    /// <summary>
    /// Coroutine that handles delayed door action completion
    /// </summary>
    private System.Collections.IEnumerator DelayedDoorAction(float delay, System.Action onCompleted)
    {
        yield return new WaitForSeconds(delay);
        onCompleted?.Invoke();
    }

    /// <summary>
    /// Public accessor for world position conversion
    /// </summary>
    public Vector3 GetWorldPositionPublic(int x, int y)
    {
        return GetWorldPosition(x, y);
    }

    /// <summary>
    /// Returns a copy of all currently spawned firefighters
    /// </summary>
    public Dictionary<int, FirefighterController> GetAllFirefighters()
    {
        return new Dictionary<int, FirefighterController>(spawnedFirefighters);
    }

}