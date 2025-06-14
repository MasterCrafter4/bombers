using System;
using System.Collections.Generic;

[Serializable]
public class GameState
{
    public int frame;
    public int turn;
    public ActionData action;
    public List<Firefighter> firefighters;
    public Grid grid;
    public List<GridChange> grid_changes;
    public List<WallDamage> wall_damage;
    public List<Door> doors;
    public List<Poi> pois;
    public Summary summary;
}

[Serializable]
public class ActionData
{
    public string type;
    public int firefighter_id;
    public int ap_before;
    public int ap_after;
    public int[] from;
    public int[] to;
    public int[] target;
    public string poi_type; 
    public string result;
    public string message;
}

[Serializable]
public class Firefighter
{
    public int id;
    public int x;
    public int y;
    public int ap;
    public bool carrying;
}

[Serializable]
public class Grid
{
    public int width;
    public int height;
    public List<Cell> cells;
}

[Serializable]
public class Cell
{
    public int x;
    public int y;
    public List<bool> walls;
    public bool door;
    public bool fire;
    public bool smoke;
    public string poi;
}

[Serializable]
public class Door
{
    public int[] from;
    public int[] to;
    public string state; 
}

[Serializable]
public class Poi
{
    public int x;
    public int y;
    public string type; // "v" o "f"
}

[Serializable]
public class WallDamage
{
    public int[] from;
    public int[] to;
    public int damage;
}

[Serializable]
public class Summary
{
    public int rescued;
    public int lost;
    public int damage;
    public int pois_active;
}


[System.Serializable]
public class GridChange
{
    public int x;
    public int y;
    public bool fire;
    public bool smoke;
    public string poi;
}

