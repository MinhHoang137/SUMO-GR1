using UnityEngine;
using System;
[Serializable]
public class EdgeData //EgdeType0
{
	public string id;
	public Coordinate startRoadLane; //Vị trí bắt đầu của làn đường cho xe đi
	public Coordinate endRoadLane; //Vị trí kết thúc của làn đường cho xe đi
	public int roadNum; // Số làn cho xe chạy
	public Coordinate startWalkingLane; //Vị trí bắt đầu của làn đường cho người đi bộ
	public Coordinate endWalkingLane; //Vị trí kết thúc của làn đường cho người đi bộ
	public int walkingNum; // Số làn cho người đi bộ
	public Coordinate direction; //Hướng của làn đường
	public Coordinate position; // Trung điểm làn bên trái cùng
}


