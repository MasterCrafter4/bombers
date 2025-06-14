using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Manages Points of Interest (POIs) including victims and valuable objects throughout the simulation.
/// Handles creation, positioning, tracking, and cleanup of POI objects on the game board.
/// </summary>
public class POIManager : MonoBehaviour
{
    [Header("POI Prefabs")]
    public GameObject victimPrefab;
    public GameObject valuablePrefab;

    [Header("Settings")]
    public float heightOffset = 0f;

    public static POIManager Instance { get; private set; }

    [Header("Debug")]
    public bool debugPOICount = true;

    private Dictionary<Vector2Int, GameObject> activePOIs = new Dictionary<Vector2Int, GameObject>();
    private int lastLoggedCount = -1;

    /// <summary>
    /// Initializes POI prefab tags and schedules initial cleanup validation
    /// </summary>
    void Start()
    {
        if (victimPrefab) victimPrefab.tag = "POI";
        if (valuablePrefab) valuablePrefab.tag = "POI";

        Invoke("ValidateAndCleanPOIs", 2.0f);
    }

    /// <summary>
    /// Sets up singleton instance pattern
    /// </summary>
    void Awake()
    {
        if (Instance == null)
            Instance = this;
        else
            Destroy(gameObject);
    }

    /// <summary>
    /// Updates or creates a POI at the specified coordinates with the given type
    /// </summary>
    public void UpdatePOI(int x, int y, string poiType)
    {
        Vector2Int position = new Vector2Int(x, y);

        if (string.IsNullOrEmpty(poiType))
        {
            RemovePOI(position);
            return;
        }

        bool poiExists = false;
        if (activePOIs.TryGetValue(position, out GameObject existingPoi))
        {
            if (existingPoi != null)
            {
                string existingType = existingPoi.name.Contains("_v_") ? "v" :
                                     existingPoi.name.Contains("_f_") ? "f" : "";

                if (existingType == poiType)
                {
                    poiExists = true;
                }
                else
                {
                    RemovePOI(position);
                }
            }
            else
            {
                activePOIs.Remove(position);
            }
        }

        if (!poiExists)
        {
            GameObject prefabToUse = null;
            if (poiType == "v")
                prefabToUse = victimPrefab;
            else if (poiType == "f")
                prefabToUse = valuablePrefab;

            if (prefabToUse != null)
            {
                CreatePOI(position, poiType, prefabToUse);
            }
        }
    }

    /// <summary>
    /// Creates a new POI instance at the specified position with appropriate scaling and positioning
    /// </summary>
    private void CreatePOI(Vector2Int position, string poiType, GameObject prefab)
    {
        Vector3 worldPos = GetWorldPosition(position.x, position.y);

        GameObject poiObject = Instantiate(prefab, worldPos, Quaternion.identity);
        poiObject.name = $"POI_{poiType}_{position.x}_{position.y}";

        float scaleValue;
        Vector3 positionOffset;
        Quaternion rotation;

        if (poiType == "v")
        {
            scaleValue = 0.5f;
            positionOffset = new Vector3(-1.33f, 0f, 6.33f);
            rotation = Quaternion.Euler(0, 180, 0);
        }
        else if (poiType == "f")
        {
            scaleValue = 1.0f;
            positionOffset = new Vector3(0f, -5.5f, 0f);
            rotation = Quaternion.Euler(0, 0, 0);
        }
        else
        {
            scaleValue = 0.5f;
            positionOffset = new Vector3(0f, 0f, 0f);
            rotation = Quaternion.identity;
        }

        poiObject.transform.localScale = new Vector3(scaleValue, scaleValue, scaleValue);
        poiObject.transform.rotation = rotation;
        poiObject.transform.position = new Vector3(
            worldPos.x + positionOffset.x,
            worldPos.y + positionOffset.y,
            worldPos.z + positionOffset.z
        );

        Rigidbody rb = poiObject.GetComponent<Rigidbody>();
        if (rb != null)
        {
            rb.isKinematic = true;
        }

        Collider[] colliders = poiObject.GetComponentsInChildren<Collider>();
        foreach (Collider col in colliders)
        {
            col.isTrigger = true;
        }

        activePOIs[position] = poiObject;

        Debug.Log($"POI creado: tipo {poiType} en ({position.x},{position.y}) con escala {scaleValue}");

        poiObject.SetActive(true);

        Renderer[] renderers = poiObject.GetComponentsInChildren<Renderer>(true);
        foreach (Renderer renderer in renderers)
        {
            renderer.enabled = true;
        }
    }

    /// <summary>
    /// Removes a POI from the specified position and destroys its game object
    /// </summary>
    public void RemovePOI(Vector2Int position)
    {
        if (activePOIs.TryGetValue(position, out GameObject poi))
        {
            Debug.Log($"POI eliminado en ({position.x},{position.y})");

            if (poi != null)
            {
                foreach (Transform child in poi.transform)
                {
                    Destroy(child.gameObject);
                }

                Destroy(poi);
            }

            activePOIs.Remove(position);
        }
    }

    /// <summary>
    /// Cleans up null references from the active POIs dictionary
    /// </summary>
    public void CleanupNullPOIs()
    {
        List<Vector2Int> toRemove = new List<Vector2Int>();

        foreach (var kvp in activePOIs)
        {
            if (kvp.Value == null)
            {
                toRemove.Add(kvp.Key);
            }
        }

        foreach (var pos in toRemove)
        {
            activePOIs.Remove(pos);
            Debug.Log($"Limpieza: POI NULL removido de ({pos.x},{pos.y})");
        }
    }

    /// <summary>
    /// Converts grid coordinates to world position using the same system as FirefighterManager
    /// </summary>
    private Vector3 GetWorldPosition(int x, int y)
    {
        if (FirefighterManager.Instance != null)
        {
            return FirefighterManager.Instance.GetWorldPositionPublic(x, y);
        }

        float scale = 2.0f;
        return new Vector3(-y * scale, heightOffset, x * scale);
    }

    /// <summary>
    /// Calculates total count of active POIs including those on the board and being carried by firefighters
    /// </summary>
    public int GetTotalActivePOIsCount()
    {
        CleanupNullPOIs();

        int poisOnBoard = activePOIs.Count;

        int poisBeingCarried = 0;
        if (FirefighterManager.Instance != null)
        {
            var firefightersList = FirefighterManager.Instance.GetAllFirefighters();
            foreach (var ff in firefightersList)
            {
                if (ff.Value != null && ff.Value.carrying)
                {
                    poisBeingCarried++;
                }
            }
        }

        int totalActivePOIs = poisOnBoard + poisBeingCarried;

        if (debugPOICount && (lastLoggedCount != totalActivePOIs || Time.frameCount % 300 == 0))
        {
            Debug.Log($"POIs activos: {poisOnBoard} en tablero + {poisBeingCarried} transportados = {totalActivePOIs} total");
            lastLoggedCount = totalActivePOIs;
        }

        return totalActivePOIs;
    }

    /// <summary>
    /// Returns a copy of the active POIs dictionary for external access
    /// </summary>
    public Dictionary<Vector2Int, GameObject> GetActivePOIs()
    {
        return new Dictionary<Vector2Int, GameObject>(activePOIs);
    }

    /// <summary>
    /// Validates and removes orphaned POI objects that exist in the scene but not in the registry
    /// </summary>
    public void ValidateAndCleanPOIs()
    {
        GameObject[] allPotentialPOIs = GameObject.FindGameObjectsWithTag("POI");
        int removedCount = 0;

        foreach (GameObject obj in allPotentialPOIs)
        {
            bool isValid = false;
            foreach (var registeredPOI in activePOIs.Values)
            {
                if (obj == registeredPOI)
                {
                    isValid = true;
                    break;
                }
            }

            if (!isValid)
            {
                Debug.LogWarning($"Eliminando POI huérfano: {obj.name}");
                Destroy(obj);
                removedCount++;
            }
        }

        if (removedCount > 0)
        {
            Debug.LogError($"ATENCIÓN: Se eliminaron {removedCount} POIs duplicados o huérfanos");
        }
    }
}