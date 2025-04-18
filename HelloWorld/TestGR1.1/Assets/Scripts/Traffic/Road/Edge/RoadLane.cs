using UnityEngine;

public class RoadLane : MonoBehaviour
{
    [SerializeField] private Transform lane;
	[SerializeField] private Transform laneMarking;
	public Transform GetLane()
	{
		return lane;
	}
	public Transform GetLaneMarking()
	{
		return laneMarking;
	}
}
