using UnityEngine;

/// <summary>
/// This Cell3D class represents a single cell in the 3D grid of the fire rescue simulation.
/// It manages visual effects for fire, smoke, and Points of Interest (POIs) within the cell.
/// </summary>
public class Cell3D : MonoBehaviour
{
    public int x;
    public int y;
    public GameObject fireEffectPrefab;
    public GameObject smokeEffectPrefab;
    public GameObject poiMarker;

    private GameObject fireInstance;
    private GameObject smokeInstance;
    private bool isOnFire = false;
    private bool isSmoked = false;
    private string poiType = null;

    /// <summary>
    /// Initializes the cell with data from JSON response.
    /// Sets the cell's position and updates fire, smoke, and POI states.
    /// </summary>
    
    public void SetData(Cell cellData)
    {
        x = cellData.x;
        y = cellData.y;

        SetFire(cellData.fire);
        SetSmoke(cellData.smoke);
        SetPOI(cellData.poi);
    }

    /// <summary>
    /// Gets the type of POI currently in this cell
    /// </summary>
    public string GetPOIType()
    {
        return poiType;
    }

    /// <summary>
    /// Sets or removes fire effect from this cell.
    /// When fire is active, any POI in the cell is automatically removed.
    /// </summary>
    public void SetFire(bool active)
    {
        if (isOnFire == active) return; // Only update if there's a change

        isOnFire = active;

        if (active)
        {
            SetPOI(null);
            if (fireInstance == null && fireEffectPrefab != null)
            {
                fireInstance = Instantiate(fireEffectPrefab, transform.position + Vector3.up * 0.1f, Quaternion.identity);
                fireInstance.transform.parent = transform;
                Debug.Log($"Cell ({x},{y}) - Fire effect created");
            }
        }
        else if (fireInstance != null)
        {
            Destroy(fireInstance);
            fireInstance = null;
            Debug.Log($"Cell ({x},{y}) - Fire effect removed");
        }
    }

    /// <summary>
    /// Sets or removes smoke effect from this cell.
    /// Creates or destroys the smoke visual effect instance based on the parameter.
    /// </summary>
    public void SetSmoke(bool hasSmoke)
    {
        if (isSmoked == hasSmoke) return; // Only update if there's a change
        
        isSmoked = hasSmoke;
        
        if (hasSmoke)
        {
            if (smokeInstance == null && smokeEffectPrefab != null)
            {
                smokeInstance = Instantiate(smokeEffectPrefab, transform.position + Vector3.up * 0.5f, Quaternion.identity);
                smokeInstance.transform.parent = transform;
                Debug.Log($"Cell ({x},{y}) - Smoke effect created");
            }
        }
        else
        {
            if (smokeInstance != null)
            {
                Destroy(smokeInstance);
                smokeInstance = null;
                Debug.Log($"Cell ({x},{y}) - Smoke effect removed");
            }
        }
    }

    /// <summary>
    /// Sets the Point of Interest (POI) type for this cell.
    /// Updates the visual POI marker and notifies the POI Manager of changes.
    /// </summary>
    public void SetPOI(string poi)
    {
        if (poiType == poi) return;
        
        poiType = poi;
        
        if (poiMarker != null)
            poiMarker.SetActive(false);
        
        if (POIManager.Instance != null)
        {
            POIManager.Instance.UpdatePOI(x, y, poi);
        }
    }
    
    /// <summary>
    /// Draws visual debugging gizmos in the Scene view.
    /// Shows red wire cubes for fire and gray wire spheres for smoke.
    /// </summary>
    private void OnDrawGizmos()
    {
        if (isOnFire)
        {
            Gizmos.color = Color.red;
            Gizmos.DrawWireCube(transform.position + Vector3.up * 0.1f, new Vector3(0.8f, 0.2f, 0.8f));
        }
        
        if (isSmoked)
        {
            Gizmos.color = new Color(0.7f, 0.7f, 0.7f, 0.5f);
            Gizmos.DrawWireSphere(transform.position + Vector3.up * 0.5f, 0.4f);
        }
    }
}