using UnityEngine;
using System.IO;

public class FrameLoader : MonoBehaviour
{
    public string folderPath = "frames"; // Carpeta dentro de StreamingAssets
    public int currentFrame = 0;
    public float timeBetweenFrames = 2f; // segundos entre cada frame

    private float timer;

    void Start()
    {
        timer = timeBetweenFrames;
    }

    void Update()
    {
        timer -= Time.deltaTime;

        if (timer <= 0f)
        {
            LoadNextFrame();
            timer = timeBetweenFrames;
        }
    }

    public void LoadNextFrame()
    {
        string fullPath = Path.Combine(Application.streamingAssetsPath, folderPath, $"frame_{currentFrame}.json");

        if (File.Exists(fullPath))
        {
            string json = File.ReadAllText(fullPath);
            GameState state = JsonUtility.FromJson<GameState>(json);
            GameManager.Instance.ApplyGameState(state);
            Debug.Log($"✅ Frame {currentFrame} cargado");
            currentFrame++;
        }
        else
        {
            Debug.Log($"🚫 No se encontró el frame {currentFrame}. Deteniendo ejecución.");
            enabled = false; // Detiene el script si no hay más frames
        }
    }
}


