using UnityEngine;

/// <summary>
/// Represents a wall segment that can be damaged or destroyed during the simulation.
/// Manages visual state changes based on damage levels and coordinate-based identification.
/// </summary>
public class WallSegment : MonoBehaviour
{
    [Header("Wall Configuration")]
    public Vector2Int cellA_coords;
    public Vector2Int cellB_coords;
    
    [Header("Damage Visualization")]
    public Material damagedMaterial;  
    
    private int currentDamage = 0;
    private Renderer wallRenderer;
    private Material originalMaterial; 
    
    /// <summary>
    /// Initializes wall renderer component and stores the original material for damage state management
    /// </summary>
    void Start()
    {
        wallRenderer = GetComponent<Renderer>();
        
        if (wallRenderer != null)
        {
            originalMaterial = wallRenderer.material;
        }
    }
    
    /// <summary>
    /// Sets the damage level of the wall and updates its visual appearance accordingly
    /// </summary>
    public void SetDamage(int damageLevel)
    {
        currentDamage = damageLevel;
        
        if (wallRenderer != null)
        {
            if (damageLevel >= 2)
            {
                gameObject.SetActive(false);
                Debug.Log($"Wall destroyed between ({cellA_coords.x},{cellA_coords.y}) and ({cellB_coords.x},{cellB_coords.y})");
            }
            else if (damageLevel == 1 && damagedMaterial != null)
            {
                wallRenderer.material = damagedMaterial;
                Debug.Log($"Wall damaged between ({cellA_coords.x},{cellA_coords.y}) and ({cellB_coords.x},{cellB_coords.y})");
            }
            else if (damageLevel == 0 && originalMaterial != null)
            {
                wallRenderer.material = originalMaterial;
                Debug.Log($"Wall repaired between ({cellA_coords.x},{cellA_coords.y}) and ({cellB_coords.x},{cellB_coords.y})");
            }
        }
    }
    
    /// <summary>
    /// Returns the current damage level of this wall segment
    /// </summary>
    public int GetCurrentDamage()
    {
        return currentDamage;
    }
    
    /// <summary>
    /// Checks if this wall segment connects the specified coordinates in either direction
    /// </summary>
    public bool MatchesCoordinates(Vector2Int from, Vector2Int to)
    {
        return (cellA_coords == from && cellB_coords == to) || 
               (cellA_coords == to && cellB_coords == from);
    }
}