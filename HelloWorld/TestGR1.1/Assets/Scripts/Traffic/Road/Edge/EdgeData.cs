using System;
using System.Collections.Generic;
using Newtonsoft.Json;
using UnityEngine;

[Serializable]
public class EdgeData
{
	[JsonProperty("i")]
	public string id;

	// Danh sách các làn đường thuộc đoạn đường (polyline-based, hỗ trợ đường cong từ OSM).
	[JsonProperty("ls")]
	public List<Lane> lanes;

	// Vị trí tâm của đoạn đường (dùng cho culling, label, vv).
	[JsonProperty("p")]
	public Coordinate position;
}

[Serializable]
public class Lane
{
	// generic | pedestrian | bicycle | bus | tram | emergency | ...
	[JsonProperty("t")]
	public string type;

	[JsonProperty("p")]
	public List<Coordinate> points;

	[JsonProperty("w")]
	public float width;
}
