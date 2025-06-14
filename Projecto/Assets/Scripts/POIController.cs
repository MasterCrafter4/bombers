// POIController.cs
using UnityEngine;

public class POIController : MonoBehaviour
{
    public int x { get; private set; }
    public int y { get; private set; }
    public string poiType { get; private set; }
    
    public void Initialize(int xPos, int yPos, string type)
    {
        x = xPos;
        y = yPos;
        poiType = type;
    }
}