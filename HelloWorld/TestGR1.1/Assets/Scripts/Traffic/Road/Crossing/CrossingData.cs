using System;
using Newtonsoft.Json;

[Serializable]
public class CrossingData
{
    [JsonProperty("i")]
    public string id;
    [JsonProperty("st")]
    public Coordinate start;
    [JsonProperty("ed")]
    public Coordinate end;
    [JsonProperty("w")]
    public float width;
    [JsonProperty("l")]
	public float length;
    [JsonProperty("d")]
    public Coordinate? direction;
}
