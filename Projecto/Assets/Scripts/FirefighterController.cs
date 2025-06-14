using UnityEngine;
using System.Collections;

/// <summary>
/// Controls individual firefighter behavior including movement, actions, and visual indicators.
/// Manages firefighter state updates and visual feedback for carrying victims.
/// </summary>
public class FirefighterController : MonoBehaviour
{
    [Header("Firefighter Data")]
    public int id;
    public int ap;
    public bool carrying;
    
    [Header("Visual Settings")]
    public float defaultMoveSpeed = 2f;
    
    [Header("Components")]
    public TextMesh idText; 
    public GameObject carryingIndicator;
    
    [Header("Action Settings")]
    public float extinguishDelay = 0.5f;  
    
    private Coroutine moveCoroutine;
    private Coroutine actionCoroutine;
    private Vector3 targetPosition;
    private bool isMoving = false;
    private bool isActing = false;
    
    /// <summary>
    /// Initializes UI components and updates visual elements on start
    /// </summary>
    void Start()
    {
        SetupUIComponents();
        UpdateVisuals();
    }
    
    /// <summary>
    /// Initializes the firefighter with basic data and sets up visual elements
    /// </summary>
    public void Initialize(int _id, int _ap, bool _carrying)
    {
        id = _id;
        ap = _ap;
        carrying = _carrying;
        
        gameObject.name = $"Firefighter_{id}";
        UpdateVisuals();
    }
    
    /// <summary>
    /// Initiates smooth movement to a target position with optional custom speed
    /// </summary>
    public void MoveTo(Vector3 newTargetPosition, float speed = -1)
    {
        if (speed < 0) speed = defaultMoveSpeed;
        
        targetPosition = newTargetPosition;
        
        if (moveCoroutine != null)
        {
            StopCoroutine(moveCoroutine);
        }
        
        moveCoroutine = StartCoroutine(MoveToPosition(targetPosition, speed));
    }
    
    /// <summary>
    /// Coroutine that handles smooth movement animation between positions
    /// </summary>
    private IEnumerator MoveToPosition(Vector3 target, float speed)
    {
        isMoving = true;
        Vector3 startPosition = transform.position;
        float distance = Vector3.Distance(startPosition, target);
        float duration = distance / speed;
        float elapsedTime = 0;
        
        while (elapsedTime < duration)
        {
            elapsedTime += Time.deltaTime;
            float progress = elapsedTime / duration;
            
            progress = Mathf.SmoothStep(0, 1, progress);
            transform.position = Vector3.Lerp(startPosition, target, progress);
            
            yield return null;
        }
        
        transform.position = target;
        isMoving = false;
        moveCoroutine = null;
    }
    
    /// <summary>
    /// Updates the firefighter's action points and refreshes visual display
    /// </summary>
    public void UpdateAP(int newAP)
    {
        ap = newAP;
        UpdateVisuals();
    }
    
    /// <summary>
    /// Sets the carrying state and manages the victim indicator visibility
    /// </summary>
    public void SetCarrying(bool isCarrying)
    {
        carrying = isCarrying;
        
        if (carrying && carryingIndicator == null)
        {
            CreateCarryingIndicator();
        }
        else if (carryingIndicator != null)
        {
            carryingIndicator.SetActive(carrying);
        }
        
        UpdateVisuals();
    }
    
    /// <summary>
    /// Creates or finds required UI components like ID text and carrying indicator
    /// </summary>
    private void SetupUIComponents()
    {
        if (idText == null)
        {
            GameObject textObj = new GameObject("ID_Text");
            textObj.transform.SetParent(transform);
            textObj.transform.localPosition = Vector3.up * 1.5f;
            
            idText = textObj.AddComponent<TextMesh>();
            idText.text = id.ToString();
            idText.fontSize = 24;
            idText.color = Color.white;
            idText.anchor = TextAnchor.MiddleCenter;
            idText.alignment = TextAlignment.Center;
            
            textObj.transform.rotation = Quaternion.LookRotation(Vector3.forward);
        }
        
        if (carryingIndicator == null && carrying)
        {
            carryingIndicator = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            carryingIndicator.transform.SetParent(transform);
            carryingIndicator.transform.localPosition = Vector3.up * 1.2f;
            carryingIndicator.transform.localScale = Vector3.one * 0.3f;
            carryingIndicator.GetComponent<Renderer>().material.color = Color.yellow;
            carryingIndicator.name = "CarryingIndicator";
            
            Destroy(carryingIndicator.GetComponent<Collider>());
        }
    }
    
    /// <summary>
    /// Checks if the firefighter is adjacent to a given position within a maximum distance
    /// </summary>
    public bool IsAdjacentTo(Vector3 position, float maxDistance = 1.5f)
    {
        Vector2 pos2D = new Vector2(transform.position.x, transform.position.z);
        Vector2 target2D = new Vector2(position.x, position.z);
        
        return Vector2.Distance(pos2D, target2D) <= maxDistance;
    }

    /// <summary>
    /// Executes fire extinguishing action with rotation towards target and timing delay
    /// </summary>
    public void ExtinguishFire(Vector3 firePosition, System.Action onCompleted = null)
    {
        if (actionCoroutine != null)
        {
            StopCoroutine(actionCoroutine);
        }
        
        actionCoroutine = StartCoroutine(ExtinguishFireRoutine(firePosition, onCompleted));
    }

    /// <summary>
    /// Coroutine that handles the fire extinguishing animation and timing
    /// </summary>
    private IEnumerator ExtinguishFireRoutine(Vector3 firePosition, System.Action onCompleted)
    {
        isActing = true;
        
        Vector3 directionToFire = firePosition - transform.position;
        directionToFire.y = 0;
        
        if (directionToFire != Vector3.zero)
        {
            transform.rotation = Quaternion.LookRotation(directionToFire);
        }
        
        yield return new WaitForSeconds(extinguishDelay);
        
        isActing = false;
        actionCoroutine = null;
        
        onCompleted?.Invoke();
    }

    /// <summary>
    /// Updates all visual elements including ID text color and carrying indicator
    /// </summary>
    private void UpdateVisuals()
    {
        if (idText != null)
        {
            idText.text = id.ToString();

            Color idColor = Color.HSVToRGB(
                (id * 0.618f) % 1.0f,
                0.8f,
                0.95f
            );
            idText.color = idColor;
        }

        if (carryingIndicator != null)
        {
            carryingIndicator.SetActive(carrying);
        }
        else if (carrying)
        {
            CreateCarryingIndicator();
        }
    }

    /// <summary>
    /// Creates a visual indicator sphere to show when the firefighter is carrying a victim
    /// </summary>
    private void CreateCarryingIndicator()
    {
        GameObject victim = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        victim.transform.SetParent(transform);
        victim.transform.localPosition = new Vector3(0, 1.4f, 0.2f);
        victim.transform.localScale = Vector3.one * 0.5f;
        
        Renderer renderer = victim.GetComponent<Renderer>();
        Material material = new Material(Shader.Find("Standard"));
        material.color = new Color(1f, 0.7f, 0f);
        material.SetFloat("_Metallic", 0.7f);
        material.SetFloat("_Glossiness", 0.8f);
        renderer.material = material;
        
        victim.name = "VictimIndicator";
        
        Destroy(victim.GetComponent<Collider>());
        
        carryingIndicator = victim;
        
        Debug.Log($"Bombero {id}: Indicador de víctima creado");
    }

    public bool IsMoving => isMoving;
    public bool IsActing => isActing;
    public Vector3 GetTargetPosition() => targetPosition;
    
    /// <summary>
    /// Cleanup coroutines when the object is destroyed
    /// </summary>
    void OnDestroy()
    {
        if (moveCoroutine != null)
        {
            StopCoroutine(moveCoroutine);
        }
    }
}