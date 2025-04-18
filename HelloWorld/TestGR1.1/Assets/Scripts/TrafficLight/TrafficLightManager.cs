using System.Collections.Generic;
using UnityEngine;

public class TrafficLightManager : MonoBehaviour
{
    public Dictionary<string, TrafficLight> trafficLightDict { get; private set; } = new Dictionary<string, TrafficLight>();
    [SerializeField] private TrafficLight trafficLightPrefab;
	[SerializeField] private TrafficLightReader trafficLightReader;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
	{
		trafficLightReader.OnReadComplete += (sender, e) =>
		{
			//Debug.Log("TrafficLightReader_OnReadComplete");
			foreach (var data in e.dataArgs)
			{
				if (trafficLightDict.TryGetValue(data.Id, out TrafficLight light))
				{
					light.SetState(data.CurrentState);
					light.SetPosition(new Vector3(data.Position[0], data.Position[1], data.Position[2]));
				}
				else
				{
					TrafficLight trafficLight = Instantiate(trafficLightPrefab);
					trafficLight.Create(data);
					trafficLight.transform.SetParent(transform);
					trafficLightDict.Add(data.Id, trafficLight);
				}
			}
		};
	}
}
