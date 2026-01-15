using System.Collections.Generic;
using UnityEngine;

public class TrafficLightManager : MonoBehaviour
{

	public static TrafficLightManager Instance { get; private set; }

	public Dictionary<string, TrafficLight> trafficLightDict { get; private set; } = new Dictionary<string, TrafficLight>();
    [SerializeField] private TrafficLight trafficLightPrefab;

	private void Awake()
	{
		if (Instance == null)
		{
			Instance = this;
		}
	}



	public void ProcessData(List<TrafficLightData> datas)
	{
		foreach (var data in datas)
		{
			if (trafficLightDict.TryGetValue(data.Id, out TrafficLight light))
			{
				light.SetState(data.CurrentState);
				light.SetPositionFromSumo(data.Position);
			}
			else
			{
				TrafficLight trafficLight = Instantiate(trafficLightPrefab);
				trafficLight.Create(data);
				trafficLight.transform.SetParent(transform);
				trafficLightDict.Add(data.Id, trafficLight);
			}
		}
	}
	private void OnDestroy()
	{
		if (Instance == this)
		{
			Instance = null;
		}
	}
}
