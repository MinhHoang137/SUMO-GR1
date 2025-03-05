using NUnit.Framework;
using System.Collections.Generic;
using UnityEngine;

public class VehicleManager : MonoBehaviour
{
	[SerializeField] private Vehicle vehiclePrefab;
	private List<Vehicle> existVehicles = new List<Vehicle>();
	private Dictionary<string, Vehicle> vehicleDict = new Dictionary<string, Vehicle>();
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		SumoClient.Instance.OnReadComplete += HandleOnReadComplete;
	}

	private void HandleOnReadComplete(object sender, SumoClient.OnReadCompleteEventArgs e)
	{
		foreach (Vehicle vehicle in existVehicles) {
			vehicle.isExist = false;
		}
		foreach (VehicleData vehicle in e.vehicles)
		{
			if (vehicleDict.TryGetValue(vehicle.id, out Vehicle existVehicle))
			{
				existVehicle.isExist = true;
				existVehicle.SetDestination(new Vector3(vehicle.position[0], 0, vehicle.position[1]));
				existVehicle.SetSpeed(vehicle.speed);
			}
			else
			{
				Vector3 position = new Vector3(vehicle.position[0], 0, vehicle.position[1]);
				Vehicle newVehicle = Instantiate(vehiclePrefab, position, Quaternion.identity);
				newVehicle.SetId(vehicle.id);
				newVehicle.SetDestination(position);
				newVehicle.SetSpeed(vehicle.speed);
				existVehicles.Add(newVehicle);
				vehicleDict.Add(vehicle.id, newVehicle);
			}
		}
		foreach (Vehicle vehicle in existVehicles)
		{
			if (!vehicle.isExist)
			{
				vehicleDict.Remove(vehicle.GetId());
				existVehicles.Remove(vehicle);
				Destroy(vehicle.gameObject);
			}
		}
	}

}
