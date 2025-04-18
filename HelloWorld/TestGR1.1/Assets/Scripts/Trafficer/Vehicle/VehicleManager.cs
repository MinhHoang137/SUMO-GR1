using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class VehicleManager : MonoBehaviour
{
	public static VehicleManager Instance { get; private set; }

	
	[SerializeField] private VehicleReader vehicleReader;
	[SerializeField] private Vehicle[] vehiclePrefabs; 
	private Dictionary<string, Vehicle> vehicleDict = new Dictionary<string, Vehicle>();

	private void Awake()
	{
		if (Instance == null)
		{
			Instance = this;
		}
	}

	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        vehicleReader.OnReadComplete += (sender, args) =>
		{
			List<Vehicle> vehicleList = new List<Vehicle>(vehicleDict.Values);
			foreach (var vehicle in vehicleList)
			{
				if (vehicle is UnityVehicle) continue;
				vehicle.isExist = false;
			}
			foreach (var data in args.data)
			{
				if (vehicleDict.TryGetValue(data.id, out Vehicle vehicle))
				{
					if (vehicle is UnityVehicle) continue;
					vehicle.Set(data);
					vehicle.isExist = true;
				}
				else
				{
					SpawnVehicle(data);
				}
			}
			try
			{
				foreach(var vehicle in vehicleList)
				{
					if (!vehicle.isExist)
					{
						DestroyVehicle(vehicle);
					}
				}
			} catch (System.InvalidOperationException e)
			{
				Debug.Log(e);
			}
		};
	}
	private void SpawnVehicle(VehicleData data)
	{
		int index = Random.Range(0, vehiclePrefabs.Length);
		Vector3 position = new Vector3(data.position[0], 0, data.position[1]);
		Vehicle vehicle = Instantiate(vehiclePrefabs[index], position, Quaternion.identity);
		vehicle.transform.forward = new Vector3(data.forward[0], 0, data.forward[1]);
		vehicle.Set(data);
		AddVehicle(vehicle);
		vehicle.transform.SetParent(transform);
	}
	private void DestroyVehicle(Vehicle v)
	{
		vehicleDict.Remove(v.GetId());
		TrafficerManager.Instance.RemoveTrafficer(v);
		Destroy(v.gameObject);
	}
	public void AddVehicle(Vehicle vehicle)
	{
		if (!vehicleDict.ContainsKey(vehicle.GetId()))
		{
			vehicleDict.Add(vehicle.GetId(), vehicle);
			TrafficerManager.Instance.AddTrafficer(vehicle);
		}
		else
		{
			Debug.LogError($"Vehicle with ID {vehicle.GetId()} already exists.");
		}
	}

	private void OnDestroy()
	{
		Instance = null;
	}
}
