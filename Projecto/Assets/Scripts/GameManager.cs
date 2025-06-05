using UnityEngine;
using System.IO;
using System.Collections.Generic;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance;
    public GameState currentState;

    void Awake()
    {
        Instance = this;
    }

    public void LoadGameStateFromFile(string path)
    {
        string json = File.ReadAllText(path);
        currentState = JsonUtility.FromJson<GameState>(json);
        Debug.Log("Estado cargado. Turno actual: " + currentState.turn);

        ApplyGameState(currentState);
    }

    public void ApplyGameState(GameState state)
    {
        if (state == null || state.action == null)
        {
            Debug.LogWarning("Estado o acción inválida");
            return;
        }

        switch (state.action.type)
        {
            case "initial_state":
                HandleInitialState(state);
                break;
            case "move":
                HandleMove(state);
                break;
            case "end_of_turn":
                HandleEndOfTurn(state);
                break;
            default:
                Debug.LogWarning("Acción no reconocida: " + state.action.type);
                break;
        }
    }

    void HandleInitialState(GameState state)
    {
        // Crear grid
        GridRenderer.Instance.BuildGrid(state.grid);

        // Spawn bomberos
        FirefighterManager.Instance.SpawnAll(state.firefighters);
    }

    void HandleMove(GameState state)
    {
        // Mover bombero(s)
        foreach (var f in state.firefighters)
        {
            var ff = FirefighterManager.Instance.GetFirefighterById(f.id);
            if (ff != null)
            {
                Vector3 pos = GridRenderer.Instance.GetCellWorldPosition(f.x, f.y);
                ff.MoveTo(pos);
                ff.UpdateAP(f.ap);
            }
        }

        // Aplicar cambios a las celdas
        foreach (var cellData in state.grid_changes)
        {
            var cell = GridRenderer.Instance.GetCell(cellData.x, cellData.y);
            if (cell != null)
            {
                cell.SetFire(cellData.fire);
                cell.SetSmoke(cellData.smoke);
                cell.SetPOI(cellData.poi);
            }
        }
    }

    void HandleEndOfTurn(GameState state)
    {
        Debug.Log("Fin del turno " + state.turn);

        // Actualizar POIs si es necesario
        foreach (var poi in state.pois)
        {
            var cell = GridRenderer.Instance.GetCell(poi.x, poi.y);
            if (cell != null)
                cell.SetPOI(poi.type);
        }

        // Otras acciones que quieras realizar: daño, HUD, etc.
    }
}


