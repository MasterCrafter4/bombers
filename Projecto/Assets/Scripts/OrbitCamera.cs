using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Provides orbit camera controls around a target object with zoom and tilt functionality.
/// Uses keyboard input for smooth camera movement and positioning.
/// </summary>
public class OrbitCamera : MonoBehaviour
{
    public Transform target;

    public float distance    = 10f;
    public float minDistance =  5f;
    public float maxDistance = 20f;

    public float orbitSpeed = 50f;
    public float zoomSpeed  = 10f;

    public float cameraHeight = 5f;
    [Range(-89f, 89f)]
    public float tiltAngle    = 30f;

    private float currentAngle = 0f;

    /// <summary>
    /// Updates camera position and rotation based on keyboard input every frame after all other updates
    /// </summary>
    void LateUpdate()
    {
        if (target == null) return;
        var kb = Keyboard.current;
        if (kb == null) return;

        if (kb.aKey.isPressed) currentAngle -= orbitSpeed * Time.deltaTime;
        if (kb.dKey.isPressed) currentAngle += orbitSpeed * Time.deltaTime;

        if (kb.wKey.isPressed) distance = Mathf.Max(minDistance, distance - zoomSpeed * Time.deltaTime);
        if (kb.sKey.isPressed) distance = Mathf.Min(maxDistance, distance + zoomSpeed * Time.deltaTime);

        float rad = currentAngle * Mathf.Deg2Rad;
        Vector3 horizontalOffset = new Vector3(
            Mathf.Sin(rad) * distance,
            0f,
            Mathf.Cos(rad) * distance
        );

        Vector3 offset = horizontalOffset + Vector3.up * cameraHeight;

        transform.position = target.position + offset;

        transform.LookAt(target);

        transform.Rotate(Vector3.right, tiltAngle, Space.Self);
    }
}