using UnityEngine;
using System;
using System.Collections.Generic;

[Serializable]
public class JunctionData
{
	public string id;
	public Coordinate position;
	public List<Coordinate> vertices;
}
