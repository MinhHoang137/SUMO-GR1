using System.Collections.Generic;
using UnityEngine;
using static UnityEngine.Rendering.GPUSort;

public class VehicleManager : MonoBehaviour
{
	public static VehicleManager Instance { get; private set; }
	[SerializeField] private Vehicle[] vehiclePrefabs;

	private Dictionary<string, Vehicle> vehicleDict = new Dictionary<string, Vehicle>();
	private Dictionary<int, Queue<Vehicle>> vehiclePool = new Dictionary<int, Queue<Vehicle>>();

	private void Awake()
	{
		if (Instance == null)
		{
			Instance = this;
		}
	}

	void Start()
	{
		// Init pool for each prefab
		for (int i = 0; i < vehiclePrefabs.Length; i++)
		{
			vehiclePool[i] = new Queue<Vehicle>();
		}
	}

	/// <summary>
	/// Handle incoming vehicle data to update, spawn, or recycle vehicles.
	/// </summary>
	/// <param name="datas"></param>
	public void ProcessData(List<VehicleData> datas)
	{
		List<Vehicle> vehicleList = new List<Vehicle>(vehicleDict.Values);
		foreach (var vehicle in vehicleList)
		{
			if (vehicle is UnityVehicle) continue;
			vehicle.isExist = false;
		}

		foreach (var data in datas)
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

		foreach (var vehicle in vehicleList)
		{
			if (!vehicle.isExist)
			{
				RecycleVehicle(vehicle);
				if (vehicle is UnityVehicle) Destroy(vehicle.gameObject);
			}
		}
	}

	private void SpawnVehicle(VehicleData data)
	{
		int index = Random.Range(0, vehiclePrefabs.Length);
		Vehicle vehicle = GetVehicleFromPool(index);
		vehicle.transform.position = new Vector3(data.position[0], 0, data.position[1]);
		vehicle.transform.forward = new Vector3(data.forward[0], 0, data.forward[1]);
		vehicle.Set(data);
		vehicle.isExist = true;
		vehicle.transform.SetParent(transform);
		vehicle.gameObject.SetActive(true);
		AddVehicle(vehicle);
	}

	private void RecycleVehicle(Vehicle vehicle)
	{
		vehicleDict.Remove(vehicle.GetId());
		TrafficerManager.Instance.RemoveTrafficer(vehicle);
		vehicle.gameObject.SetActive(false);
		int prefabIndex = GetVehiclePrefabIndex(vehicle);
		if (prefabIndex != -1 && vehicle is not UnityVehicle)
		{
			vehiclePool[prefabIndex].Enqueue(vehicle);
		}
	}

	private Vehicle GetVehicleFromPool(int prefabIndex)
	{
		if (vehiclePool[prefabIndex].Count > 0)
		{
			return vehiclePool[prefabIndex].Dequeue();
		}
		else
		{
			return Instantiate(vehiclePrefabs[prefabIndex]);
		}
	}

	private int GetVehiclePrefabIndex(Vehicle vehicle)
	{
		for (int i = 0; i < vehiclePrefabs.Length; i++)
		{
			if (vehicle.name.Contains(vehiclePrefabs[i].name))
			{
				return i;
			}
		}
		return -1;
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
