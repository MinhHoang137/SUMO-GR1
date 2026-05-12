using UnityEngine;
using System;
using Newtonsoft.Json;

[Serializable]
public class EdgeData //EgdeType0
{
	[JsonProperty("i")]
	public string id;
	[JsonProperty("sr")]
	public Coordinate startRoadLane; //Vị trí bắt đầu của làn đường cho xe đi
	[JsonProperty("er")]
	public Coordinate endRoadLane; //Vị trí kết thúc của làn đường cho xe đi
	[JsonProperty("rn")]
	public int roadNum; // Số làn cho xe chạy
	[JsonProperty("sw")]
	public Coordinate? startWalkingLane; //Vị trí bắt đầu của làn đường cho người đi bộ
	[JsonProperty("ew")]
	public Coordinate? endWalkingLane; //Vị trí kết thúc của làn đường cho người đi bộ
	[JsonProperty("wn")]
	public int walkingNum; // Số làn cho người đi bộ
	[JsonProperty("d")]
	public Coordinate direction; //Hướng của làn đường
	[JsonProperty("p")]
	public Coordinate position; // Trung điểm làn bên trái cùng
}


