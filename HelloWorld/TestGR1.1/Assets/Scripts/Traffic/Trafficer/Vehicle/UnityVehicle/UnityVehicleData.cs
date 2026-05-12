using System;
using Newtonsoft.Json;

[Serializable]
public class UnityVehicleData
{
	[JsonProperty("i")]
	public string id;
	[JsonProperty("p")]
	public float[] position;
	[JsonProperty("f")]
	public float[] forward;
	[JsonProperty("sp")]
	public float speed;
	[JsonProperty("e")]
	public bool isExist;

	public UnityVehicleData(string id, float[] position, float[] forward, float speed, bool isExist = true)
	{
		this.id = id;
		this.position = position;
		this.forward = forward;
		this.speed = speed;
		this.isExist = isExist;
	}
}
