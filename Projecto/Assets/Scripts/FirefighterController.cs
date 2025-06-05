using UnityEngine;

public class FirefighterController : MonoBehaviour
{
    public int id;
    public int ap;
    public bool carrying;

    public void Initialize(int _id, int _ap, bool _carrying)
    {
        id = _id;
        ap = _ap;
        carrying = _carrying;
    }

    public void MoveTo(Vector3 targetPosition)
    {
        transform.position = targetPosition;
    }

    public void UpdateAP(int newAP)
    {
        ap = newAP;
        // aquí podrías actualizar el HUD del bombero, etc.
    }
}
