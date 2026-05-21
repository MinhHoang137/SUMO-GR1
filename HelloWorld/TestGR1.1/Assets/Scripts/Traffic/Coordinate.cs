using System;
using UnityEngine;
using Newtonsoft.Json;

[Serializable]
public struct Coordinate
{
	[JsonProperty("x")]
	public float x;
	[JsonProperty("y")]
	public float y;
	[JsonProperty("z")]
	public float z;
}