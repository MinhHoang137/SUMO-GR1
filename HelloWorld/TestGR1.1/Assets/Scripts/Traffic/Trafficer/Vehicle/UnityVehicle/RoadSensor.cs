using UnityEngine;
using System.Collections.Generic;

[RequireComponent(typeof(Rigidbody))]
public class RoadSensor : Sensor
{
	private List<Road> roads = new();
	private void OnTriggerEnter(Collider other)
	{
		//Debug.Log("RoadSensor: OnTriggerEnter");
		if (other.transform.GetComponentInParent<Road>() is Road road)
		{
			roads.Add(road);
			if (roads.Count > 0)
			{
				canMove = true;
			}
		}
	}
	private void OnTriggerExit(Collider other)
	{
		if (other.transform.GetComponentInParent<Road>() is Road road)
		{
			roads.Remove(road);
			if (roads.Count == 0)
			{
				canMove = false;
			}
		}
	}
	public override bool CanMove()
	{
		return roads.Count > 0;
	}
}
