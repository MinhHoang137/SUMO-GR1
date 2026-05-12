using UnityEngine;
using System;
using System.Collections.Generic;
using Newtonsoft.Json;

[Serializable]
public class JunctionData
{
	[Serializable]
	public class Vertex
	{
		[JsonProperty("x")]
		public float x;
		[JsonProperty("y")]
		public float y;
	}
	[JsonProperty("i")]
	public string id;
	[JsonProperty("p")]
	public float[] position;
	[JsonProperty("v")]
	public List<Vertex> vertices;
}
