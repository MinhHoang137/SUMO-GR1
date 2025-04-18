using UnityEngine;
using System;
using System.Collections.Generic;

[Serializable]
public class JunctionData
{
	[Serializable]
	public class Vertex
	{
		public float x;
		public float y;
	}
	public string id;
	public float[] position;
	public List<Vertex> vertices;
}
