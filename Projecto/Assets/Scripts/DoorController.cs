using UnityEngine;

/// <summary>
/// Controls door behavior including opening, closing, and destruction animations.
/// Manages door state changes and visual feedback for fire rescue simulation.
/// </summary>
public class DoorController : MonoBehaviour
{
    [Header("Door Configuration")]
    public Vector2Int cellA_coords;
    public Vector2Int cellB_coords;
    
    [Header("Door Type")]
    public bool isEntry = false;
    
    [Header("Door Components")]
    public Transform doorPivot;
    public Collider doorCollider;
    
    [Header("Animation Settings")]
    public float openAngle = -90f;
    public float animationSpeed = 2f;
    
    [Header("Debug")]
    [SerializeField] private string debugState = "unknown";
    
    private string currentState = "unknown";
    private bool isAnimating = false;
    
    /// <summary>
    /// Initializes door components and sets up entry doors as permanently open
    /// </summary>
    void Start()
    {
        if (doorCollider == null)
            doorCollider = GetComponentInChildren<Collider>();
        
        if (doorPivot == null)
        {
            Debug.LogError($"Door {name} at ({cellA_coords.x},{cellA_coords.y})-({cellB_coords.x},{cellB_coords.y}) has NO PIVOT ASSIGNED!");
        }
            
        if (isEntry)
        {
            SetupAsEntry();
        }
        else
        {
            currentState = "unknown"; 
            debugState = "unknown";   
        }
    }
        
    /// <summary>
    /// Configures the door as an entry door with permanent open state
    /// </summary>
    private void SetupAsEntry()
    {
        currentState = "open";
        debugState = "open (entry)";
        
        if (doorCollider != null)
            doorCollider.enabled = false;
            
        if (doorPivot != null)
        {
            doorPivot.localRotation = Quaternion.Euler(0, openAngle, 0);
        }
        else
        {
            Debug.LogError($"Entry door {name} at ({cellA_coords.x},{cellA_coords.y})-({cellB_coords.x},{cellB_coords.y}) has NO PIVOT ASSIGNED!");
        }
    }
    
    /// <summary>
    /// Changes the door state to open, closed, or destroyed with appropriate animations
    /// </summary>
    public void SetDoorState(string newState)
    {
        if (isEntry)
        {
            return;
        }
        
        if (doorPivot == null)
        {
            Debug.LogError($"Door {name} has no pivot assigned! Cannot change state to {newState}");
            return;
        }
        
        if (currentState == newState)
        {
            return;
        }
        
        if (isAnimating)
        {
            Debug.Log($"Door {name} is currently animating - queuing state change to {newState} not implemented");
            return;
        }
            
        Debug.Log($"Door {name} state changing from {currentState} to {newState}");
        currentState = newState;
        debugState = newState;
        
        switch (newState.ToLower())
        {
            case "open":
                OpenDoor();
                break;
            case "closed":
                CloseDoor();
                break;
            case "destroyed":
                DestroyDoor();
                break;
            default:
                Debug.LogWarning($"Unknown door state: {newState} for door {name}");
                break;
        }
    }
    
    /// <summary>
    /// Gets the current state of the door
    /// </summary>
    public string GetCurrentState()
    {
        return currentState;
    }
    
    /// <summary>
    /// Checks if this door connects the specified coordinates
    /// </summary>
    public bool MatchesCoordinates(Vector2Int from, Vector2Int to)
    {
        return (cellA_coords == from && cellB_coords == to) || 
               (cellA_coords == to && cellB_coords == from);
    }
    
    /// <summary>
    /// Returns whether this door is marked as an entry door
    /// </summary>
    public bool IsEntry()
    {
        return isEntry;
    }
    
    /// <summary>
    /// Opens the door by rotating it and disabling collision
    /// </summary>
    private void OpenDoor()
    {
        if (doorPivot != null)
        {
            StartCoroutine(RotateDoor(openAngle));
        }
        else
        {
            Debug.LogError($"Door {name} has no pivot to rotate for OpenDoor!");
        }
        
        if (doorCollider != null)
        {
            doorCollider.enabled = false;
        }
        else
        {
            Debug.LogWarning($"Door {name} has no collider to disable!");
        }
    }
    
    /// <summary>
    /// Closes the door by rotating it back and enabling collision
    /// </summary>
    private void CloseDoor()
    {
        if (doorPivot != null)
        {
            StartCoroutine(RotateDoor(0f));
        }
        else
        {
            Debug.LogError($"Door {name} has no pivot to rotate for CloseDoor!");
        }
        
        if (doorCollider != null)
        {
            doorCollider.enabled = true;
        }
        else
        {
            Debug.LogWarning($"Door {name} has no collider to enable!");
        }
    }
    
    /// <summary>
    /// Destroys the door by disabling collision and hiding all visual components
    /// </summary>
    private void DestroyDoor()
    {
        Debug.Log($"Door {name}: DestroyDoor() called");
        
        if (doorCollider != null)
        {
            doorCollider.enabled = false;
        }
            
        Renderer[] renderers = GetComponentsInChildren<Renderer>();
        foreach (var renderer in renderers)
        {
            renderer.enabled = false;
        }
    }
    
    /// <summary>
    /// Smoothly rotates the door to the target angle over time
    /// </summary>
    private System.Collections.IEnumerator RotateDoor(float targetAngle)
    {
        if (isEntry) 
        {
            yield break;
        }
        
        isAnimating = true;
        
        Quaternion startRotation = doorPivot.localRotation;
        Quaternion targetRotation = Quaternion.Euler(0, targetAngle, 0);
        
        float elapsedTime = 0f;
        float duration = 1f / animationSpeed; 
        if (animationSpeed <= 0) duration = 1f; 
        
        while (elapsedTime < duration)
        {
            doorPivot.localRotation = Quaternion.Slerp(startRotation, targetRotation, elapsedTime / duration);
            elapsedTime += Time.deltaTime;
            yield return null;
        }
        
        doorPivot.localRotation = targetRotation;
        isAnimating = false;
    }
        
    /// <summary>
    /// Draws visual gizmos in the editor to show door state and orientation
    /// </summary>
    #if UNITY_EDITOR
    private void OnDrawGizmos()
    {
        if (doorPivot == null) return;
        
        Gizmos.color = currentState == "open" ? Color.green : 
                        currentState == "closed" ? Color.red :
                        currentState == "destroyed" ? Color.gray : Color.yellow;
                        
        Vector3 doorCenter = doorPivot.position + Vector3.up * 0.5f;
        Gizmos.DrawSphere(doorCenter, 0.2f);
        Gizmos.DrawLine(doorCenter, doorCenter + doorPivot.forward * 0.5f);
    }
    #endif
}