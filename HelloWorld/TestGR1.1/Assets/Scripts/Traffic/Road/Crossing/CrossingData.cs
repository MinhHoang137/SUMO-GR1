using System;

[Serializable]
public class CrossingData
{
    public string id;
    public Coordinate start;
    public Coordinate end;
    public float width;
	public float length;
    public Coordinate? direction;
}
