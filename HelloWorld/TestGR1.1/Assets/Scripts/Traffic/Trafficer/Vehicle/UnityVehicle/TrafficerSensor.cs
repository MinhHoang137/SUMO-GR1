using UnityEngine;
using System.Collections.Generic;

public class TrafficerSensor : Sensor
{
	private List<Trafficer> trafficers = new List<Trafficer>();
	private void OnTriggerExit(Collider other)
	{
		if (other.transform.TryGetComponent(out Trafficer vehicle))
		{
			trafficers.Remove(vehicle);
			canMove = trafficers.Count == 0;
		}
	}
	private void OnTriggerEnter(Collider other)
	{
		if (other.transform.TryGetComponent(out Trafficer v))
		{
			trafficers.Add(v);
			canMove = trafficers.Count == 0;
		}
	}
	public override bool CanMove()
	{
		return trafficers.Count == 0;
	}
}