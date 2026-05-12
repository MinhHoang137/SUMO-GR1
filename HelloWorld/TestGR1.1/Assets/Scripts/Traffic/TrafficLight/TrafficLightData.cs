using UnityEngine;
using System;
using Newtonsoft.Json;

[Serializable]
public class TrafficLightData : ObjectData
{
	[JsonProperty("i")]
	[SerializeField] private string id;

	[JsonProperty("p")]
	[SerializeField] private float[] position;

	[JsonProperty("d")]
	[SerializeField] private float[] direction;

	[JsonProperty("s")]
	[SerializeField] private int state; // 0: Red, 1: Yellow, 2: Green
	public string Id => id;
	public float[] Position => position;
	public int CurrentState => state;
	public float[] Direction => direction;
}
