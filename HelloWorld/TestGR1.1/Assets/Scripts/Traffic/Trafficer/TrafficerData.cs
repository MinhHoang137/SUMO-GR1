using System;
using Newtonsoft.Json;

[Serializable]
public class TrafficerData: ObjectData
{
	[JsonProperty("i")]
	public string id;
	[JsonProperty("p")]
	public float[] position;
	[JsonProperty("sp")]
	public float speed;
	[JsonProperty("f")]
	public float[] forward;
	public TrafficerData(string id, string type, float[] position, float[] forward, float speed)
	{
		this.id = id;
		this.type = type;
		this.position = position;
		this.speed = speed;
		this.forward = forward;
	}
}