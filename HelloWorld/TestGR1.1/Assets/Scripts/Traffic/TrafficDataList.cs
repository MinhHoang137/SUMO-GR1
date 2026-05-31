using UnityEngine;
using System;
using System.Collections.Generic;
using Newtonsoft.Json;

/**
 * A serializable class that holds a list of Traffic objects.
 * use for receiving traffic data from external sources only.
 */
[Serializable]
public class TrafficDataList
{
    [JsonProperty("st")]
    [SerializeField] private int step = 0;

    [JsonProperty("tl")]
    [SerializeField] private List<TrafficLightData> trafficLights = new ();

	[JsonProperty("tr")]
	[SerializeField] private List<TrafficerData> trafficers = new ();

	public int Step => step;
	public List<TrafficLightData> TrafficLights => trafficLights;
	public List<TrafficerData> Trafficers => trafficers;
}
