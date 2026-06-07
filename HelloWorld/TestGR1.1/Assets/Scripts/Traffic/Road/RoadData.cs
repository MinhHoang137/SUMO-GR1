using System.Collections.Generic;
using System;
using UnityEngine;
using Newtonsoft.Json;

/*
	Class lưu trữ dữ liệu của toàn bộ hệ thống đường bao gồm:
	- JunctionData: Dữ liệu về các giao lộ
	- EdgeData: Dữ liệu về các đoạn đường
	- CrossingData: Dữ liệu về các vạch qua đường dành cho người đi bộ
    Chỉ dùng để truyền dữ liệu, không chứa logic xử lý nào.
*/
[Serializable]
public class RoadData
{
	[JsonProperty("jd")]
	public List<JunctionData> junctionDatas;
	[JsonProperty("ed")]
	public List<EdgeData> edgeDatas;
	[JsonProperty("cd")]
	public List<CrossingData> crossingDatas;
	// Toà nhà — chỉ có ở chế độ render OSM; null/rỗng ở benchmark & custom-script.
	[JsonProperty("bd")]
	public List<BuildingData> buildingDatas;

	public List<JunctionData> JunctionDatas => junctionDatas;
	public List<EdgeData> EdgeDatas => edgeDatas;
	public List<CrossingData> CrossingDatas => crossingDatas;
	public List<BuildingData> BuildingDatas => buildingDatas;
}
