using NUnit.Framework;
using System.Collections.Generic;
using UnityEngine;
using System;

public class TrafficerManager : MonoBehaviour
{
	public static TrafficerManager Instance { get; private set; }
	public const string CAR = "Car";
	public const string PEDESTRIAN = "Pedestrian";

	[SerializeField] private Car[] carPrefabs;
	[SerializeField] private Pedestrian[] pedestrianPrefabs;
	private List<Trafficer> existTrafficers = new List<Trafficer>();
	private Dictionary<string, Trafficer> trafficerDict = new Dictionary<string, Trafficer>();

	private void Awake()
	{
		Instance = this;
	}

	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		TrafficerReader.Instance.OnReadComplete += HandleOnReadComplete;
	}

	private void HandleOnReadComplete(object sender, TrafficerReader.OnReadCompleteEventArgs e)
	{
		foreach (Trafficer trafficer in existTrafficers)
		{
			trafficer.isExist = false;
		}
		foreach (TrafficerData trafficer in e.trafficers)
		{
			if (trafficerDict.TryGetValue(trafficer.id, out Trafficer tr))
			{
				tr.isExist = true;
				tr.Set(trafficer);
			}
			else
			{
				if (trafficer.type == CAR)
				{
					int index = UnityEngine.Random.Range(0, carPrefabs.Length);
					SpawnCar(carPrefabs[index], trafficer);
				}
				else if (trafficer.type == PEDESTRIAN)
				{
					int index = UnityEngine.Random.Range(0, pedestrianPrefabs.Length);
					SpawnPedestrian(pedestrianPrefabs[index], trafficer);
				}
			}
		}
		try
		{
			foreach (Trafficer trafficer in existTrafficers)
			{
				if (!trafficer.isExist)
				{
					DestroyTrafficer(trafficer);
				}
			}
		}
		catch (Exception err)
		{
			Debug.Log(err);
		}
	}
	private void SpawnCar(Car car, TrafficerData carData)
	{
		Vector3 position = new Vector3(carData.position[0], 0, carData.position[1]);
		Car newCar = Instantiate(car, position, Quaternion.identity);
		newCar.Set(carData);
		existTrafficers.Add(newCar);
		trafficerDict.Add(newCar.GetId(), newCar);
	}
	private void SpawnPedestrian(Pedestrian pedestrian, TrafficerData p)
	{
		Vector3 position = new Vector3(p.position[0], 0, p.position[1]);
		Pedestrian newPedestrian = Instantiate(pedestrian, position, Quaternion.identity);
		newPedestrian.Set(p);
		existTrafficers.Add(newPedestrian);
		trafficerDict.Add(newPedestrian.GetId(), newPedestrian);
	}
	public List<Trafficer> GetTrafficers()
	{
		return existTrafficers;
	}
	private void DestroyTrafficer(Trafficer trafficer)
	{
		trafficerDict.Remove(trafficer.GetId());
		existTrafficers.Remove(trafficer);
		Destroy(trafficer.gameObject);
	}
}
