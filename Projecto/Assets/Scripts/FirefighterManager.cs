using UnityEngine;
using System.Collections.Generic;

public class FirefighterManager : MonoBehaviour
{
    public static FirefighterManager Instance;

    public GameObject firefighterPrefab;
    private Dictionary<int, FirefighterController> firefighters = new();

    void Awake()
    {
        Instance = this;
    }

    public void SpawnAll(List<Firefighter> firefighterData)
    {
        foreach (var data in firefighterData)
        {
            GameObject go = Instantiate(firefighterPrefab, new Vector3(data.x, 0.5f, data.y), Quaternion.identity);
            FirefighterController controller = go.GetComponent<FirefighterController>();
            controller.Initialize(data.id, data.ap, data.carrying);
            firefighters[data.id] = controller;
        }
    }

    public FirefighterController GetFirefighterById(int id)
    {
        return firefighters.ContainsKey(id) ? firefighters[id] : null;
    }
}
