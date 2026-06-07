using UnityEngine;
using System.Collections.Generic;
using System;

[CreateAssetMenu(fileName = "RoadData", menuName = "Scriptable Objects/RoadData")]
public class RoadDataSO : ScriptableObject
{
    public List<JunctionData> junctionDatas;
	public List<EdgeData> edgeDatas;
	public List<CrossingData> crossingDatas;
	public List<BuildingData> buildingDatas;
}
