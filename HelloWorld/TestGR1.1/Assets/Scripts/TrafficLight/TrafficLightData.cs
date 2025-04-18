using UnityEngine;
using System;
using Newtonsoft.Json;

[Serializable]
public class TrafficLightData
{
	[JsonProperty("id")]
	[SerializeField] private string id;

	[JsonProperty("position")]
	[SerializeField] private float[] position;

	[JsonProperty("direction")]
	[SerializeField] private float[] direction;

	[JsonProperty("state")]
	[SerializeField] private int state; // 0: Red, 1: Yellow, 2: Green
	public string Id => id;
	public float[] Position => position;
	public int CurrentState => state;
	public float[] Direction => direction;
}
