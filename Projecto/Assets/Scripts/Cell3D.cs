using UnityEngine;

public class Cell3D : MonoBehaviour
{
    public int x;
    public int y;

    // Prefabs para efectos
    public GameObject fireEffectPrefab;
    public GameObject smokeEffectPrefab;

    // Instancias activas
    private GameObject fireInstance;
    private GameObject smokeInstance;

    // Marcador de POI
    public GameObject poiMarker;

    private bool isOnFire = false;
    private bool isSmoked = false;
    private string poiType = null;

    // Método para inicializar la celda desde datos JSON
    public void SetData(Cell cellData)
    {
        x = cellData.x;
        y = cellData.y;

        SetFire(cellData.fire);
        SetSmoke(cellData.smoke);
        SetPOI(cellData.poi);
    }

    public void SetFire(bool active)
    {
        isOnFire = active;

        if (active)
        {
            if (fireInstance == null && fireEffectPrefab != null)
            {
                fireInstance = Instantiate(fireEffectPrefab, transform.position, Quaternion.identity, transform);
            }
        }
        else if (fireInstance != null)
        {
            Destroy(fireInstance);
            fireInstance = null;
        }
    }

    public void SetSmoke(bool active)
    {
        isSmoked = active;

        if (active)
        {
            if (smokeInstance == null && smokeEffectPrefab != null)
            {
                smokeInstance = Instantiate(smokeEffectPrefab, transform.position, Quaternion.identity, transform);
            }
        }
        else if (smokeInstance != null)
        {
            Destroy(smokeInstance);
            smokeInstance = null;
        }
    }

    public void SetPOI(string poi)
    {
        poiType = poi;

        if (poiMarker != null)
        {
            if (string.IsNullOrEmpty(poi))
            {
                poiMarker.SetActive(false);
            }
            else
            {
                poiMarker.SetActive(true);

                // Opcional: cambiar color o símbolo del POI dependiendo del tipo
                SpriteRenderer renderer = poiMarker.GetComponent<SpriteRenderer>();
                if (renderer != null)
                {
                    if (poi == "v")
                        renderer.color = Color.green;
                    else if (poi == "f")
                        renderer.color = Color.red;
                    else
                        renderer.color = Color.yellow;
                }
            }
        }
    }
}



