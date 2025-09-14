using UnityEngine;
using System;
using System.Collections.Generic;

/**
 * A serializable class that holds a list of Traffic objects.
 * use for receiving traffic data from external sources only.
 */
[Serializable]
public class TrafficDataList
{
    [SerializeField] private List<TrafficLightData> trafficLights = new ();
	[SerializeField] private List<VehicleData> vehicles = new ();
	[SerializeField] private List<PedestrianData> pedestrians = new();
	public List<TrafficLightData> TrafficLights => trafficLights;
	public List<VehicleData> Vehicles => vehicles;
	public List<PedestrianData> Pedestrians => pedestrians;
}
