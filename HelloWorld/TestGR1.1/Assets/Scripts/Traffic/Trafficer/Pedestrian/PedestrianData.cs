using System;
using UnityEngine;

[Serializable]
public class PedestrianData: TrafficerData
{
    public PedestrianData(string id, string type, 
		float[] position, float[] forward, 
		float speed, string lane) 
		: base(id, type, position, forward, speed, lane)
	{

	}
}
