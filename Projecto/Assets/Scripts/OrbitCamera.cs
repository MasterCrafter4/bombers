using UnityEngine;
using UnityEngine.InputSystem;

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

    void LateUpdate()
    {
        if (target == null) return;
        var kb = Keyboard.current;
        if (kb == null) return;

        // Orbitar
        if (kb.aKey.isPressed) currentAngle -= orbitSpeed * Time.deltaTime;
        if (kb.dKey.isPressed) currentAngle += orbitSpeed * Time.deltaTime;

        // Zoom
        if (kb.wKey.isPressed) distance = Mathf.Max(minDistance, distance - zoomSpeed * Time.deltaTime);
        if (kb.sKey.isPressed) distance = Mathf.Min(maxDistance, distance + zoomSpeed * Time.deltaTime);

        // Calcular offset horizontal
        float rad = currentAngle * Mathf.Deg2Rad;
        Vector3 horizontalOffset = new Vector3(
            Mathf.Sin(rad) * distance,
            0f,
            Mathf.Cos(rad) * distance
        );

        // Offset total con altura
        Vector3 offset = horizontalOffset + Vector3.up * cameraHeight;

        // 1) Posicionar la cámara
        transform.position = target.position + offset;

        // 2) Mirar siempre al target
        transform.LookAt(target);

        // 3) Inclinar (tilt) sobre el eje local X
        transform.Rotate(Vector3.right, tiltAngle, Space.Self);
    }
}
