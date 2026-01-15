using UnityEngine;
using System;
using Newtonsoft.Json;

[Serializable]
public class TrafficLightData : ObjectData
{
	[JsonProperty("id")]
	[SerializeField] private string id;

	[JsonProperty("position")]
	[SerializeField] private Coordinate position;

	[JsonProperty("direction")]
	[SerializeField] private Coordinate direction;

	[JsonProperty("state")]
	[SerializeField] private int state; // 0: Red, 1: Yellow, 2: Green
	public string Id => id;
	public Coordinate Position => position;
	public int CurrentState => state;
	public Coordinate Direction => direction;
}
