using System;
using System.Collections.Generic;
using Newtonsoft.Json;

/*
	Dữ liệu một toà nhà trích từ .osm (chỉ có ở chế độ render OSM).
	Toạ độ đỉnh ở hệ net SUMO (x, y, z) — z là cao độ nền. Unity dựng mesh bằng
	cách extrude polygon đáy lên cao `height` (xem Building.cs).
*/
[Serializable]
public class BuildingData
{
	[JsonProperty("i")]
	public string id;
	[JsonProperty("h")]
	public float height;
	[JsonProperty("v")]
	public List<Coordinate> vertices;
}
