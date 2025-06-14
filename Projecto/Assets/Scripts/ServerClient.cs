using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System;
using UnityEngine.InputSystem;

public class ServerClient : MonoBehaviour
{
    public static ServerClient Instance;

    [Header("Server Configuration")]
    public string serverUrl = "http://localhost:8585";
    public bool showDebugMessages = true;

    // Events for communication 
    public static event Action<StepR> OnStepReceived;
    public static event Action<string> OnSimulationFinished;
    public static event Action<string> OnConnectionError;

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    /// <summary>
    /// Send step request to Python server
    /// </summary>
    public void RequestNextStep()
    {
        StartCoroutine(SendStepRequest());
    }

    // IEnumerator - yield return
    IEnumerator SendStepRequest()
    {
        WWWForm form = new WWWForm();
        form.AddField("action", "step");

        string url = serverUrl + "/step";

        using (UnityWebRequest www = UnityWebRequest.Post(url, form))
        {
            // Upload/download handler pattern
            www.downloadHandler = (DownloadHandler)new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");

            yield return www.SendWebRequest();

            // Error handling following
            if (www.result == UnityWebRequest.Result.ConnectionError || www.result == UnityWebRequest.Result.ProtocolError)
            {
                string errorMsg = $"Connection error: {www.error}";
                if (showDebugMessages)
                    Debug.Log(errorMsg);

                OnConnectionError?.Invoke(errorMsg);
            }
            else
            {
                if (showDebugMessages)
                    Debug.Log("Server response: " + www.downloadHandler.text);    // Answer from Python

                // Process the response 
                ProcessServerResponse(www.downloadHandler.text);
            }
        }
    }

    /// <summary>
    /// Process server response - JSON parsing approach
    /// </summary>
    void ProcessServerResponse(string jsonResponse)
    {
        try
        {
            // Check if simulation is finished
            if (jsonResponse.Contains("Simulation finished"))
            {
                FinishedR finishedR = JsonUtility.FromJson<FinishedR>(jsonResponse);
                string message = $"Simulation finished at step {finishedR.step}: {finishedR.message}";

                if (showDebugMessages)
                    Debug.Log(message);

                OnSimulationFinished?.Invoke(message);
                return;
            }

            // Parse normal step response
            StepR stepR = JsonUtility.FromJson<StepR>(jsonResponse.Replace('\'', '\"'));

            if (stepR != null)
            {
                if (showDebugMessages)
                    Debug.Log($"Parsed turn {stepR.turn} with {stepR.total_frames} frames");

                OnStepReceived?.Invoke(stepR);
            }
            else
            {
                OnConnectionError?.Invoke("Failed to parse server response");
            }
        }
        catch (System.Exception e)
        {
            string errorMsg = $"JSON parsing error: {e.Message}";
            if (showDebugMessages)
                Debug.Log(errorMsg);

            OnConnectionError?.Invoke(errorMsg);
        }
    }

    /// <summary>
    /// Test connection to server
    /// </summary>
    public void TestConnection()
    {
        StartCoroutine(SendTestRequest());
    }

    IEnumerator SendTestRequest()
    {
        if (showDebugMessages)
            Debug.Log($"Testing connection to: {serverUrl}");

        using (UnityWebRequest www = UnityWebRequest.Get(serverUrl))
        {
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.ConnectionError || www.result == UnityWebRequest.Result.ProtocolError)
            {
                string errorMsg = $"Server not reachable: {www.error}";
                if (showDebugMessages)
                    Debug.Log(errorMsg);

                OnConnectionError?.Invoke(errorMsg);
            }
            else
            {
                if (showDebugMessages)
                    Debug.Log("Server connection successful");
            }
        }
    }

    // Start pattern for initial setup
    void Start()
    {
        if (showDebugMessages)
            Debug.Log("ServerClient initialized for Fire Rescue simulation");

        // Test connection on start 
        TestConnection();
    }

    void Update()
    {
        if (Keyboard.current.spaceKey.wasPressedThisFrame)
        {
            if (showDebugMessages)
                Debug.Log("Tecla Espacio presionada (Input System). Solicitando siguiente paso...");
            RequestNextStep();
        }
    }

}

[System.Serializable]
public class StepR
{
    public int turn;
    public int total_frames;
    public List<GameState> frames;
    public Summary summary;
}

[System.Serializable]
public class FinishedR
{
    public string message;
    public int step;
}