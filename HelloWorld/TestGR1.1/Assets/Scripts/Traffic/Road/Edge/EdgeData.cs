using UnityEngine;
using System;
using System.Collections.Generic;
[Serializable]
public class EdgeData //EgdeType0
{
	public string id;
	public List<Lane> lanes; // Danh sách các làn đường thuộc đoạn đường này
	public Coordinate position; // Vị trí của làn đường, coi như trọng tâm của đoạn đường
}

[Serializable]
public class Lane
{
	public string type; // generic (for many types of vehicles), pedestrian, bicycle, bus, tram, emergency, etc.
	public List<Coordinate> points; // Danh sách các điểm tạo thành làn đường
	public float width; // Chiều rộng của làn đường
}


