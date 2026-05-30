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
	public ExistState state;

	public UnityVehicleData(string id, float[] position, float[] forward, float speed, ExistState state = ExistState.ServerControlled)
	{
		this.id = id;
		this.position = position;
		this.forward = forward;
		this.speed = speed;
		this.state = state;
	}
}
