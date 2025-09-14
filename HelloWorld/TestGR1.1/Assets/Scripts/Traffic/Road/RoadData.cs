using System.Collections.Generic;
using System;
using UnityEngine;

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
	public List<JunctionData> junctionDatas;
	public List<EdgeData> edgeDatas;
	public List<CrossingData> crossingDatas;

	public List<JunctionData> JunctionDatas => junctionDatas;
	public List<EdgeData> EdgeDatas => edgeDatas;
	public List<CrossingData> CrossingDatas => crossingDatas;
}
