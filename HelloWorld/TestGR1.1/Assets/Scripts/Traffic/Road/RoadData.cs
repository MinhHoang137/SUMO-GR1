using UnityEngine;
using System.Collections.Generic;

[CreateAssetMenu(fileName = "RoadData", menuName = "Scriptable Objects/RoadData")]
public class RoadData : ScriptableObject
{
    public List<JunctionData> junctionDatas;
	public List<EdgeData> edgeDatas;
	public List<CrossingData> crossingDatas;
}
