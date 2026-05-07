using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using System.Collections.Generic;

public class UnityVehicleManager : MonoBehaviour
{
	private const string CMD_CREATE = "Tạo xe Unity";

	private UnityVehicle vehicle = null;
    [SerializeField] private Button stateButton;
	[SerializeField] private TMP_Text stateText;
    [SerializeField] private UnityVehicle prefab;
	[SerializeField] private VehicleSender vehicleSender;
	[SerializeField] private RoadDataSO roadData;
	[SerializeField] private List<Vector3> junctionPos = new List<Vector3>();

	private void Start()
	{
		stateText.text = CMD_CREATE;
		stateButton.onClick.AddListener(() =>
		{
			if (vehicle == null)
			{
				Create();
			}
			else
			{
				Destroy();
			}
		});
		StartCoroutine(ManipulateAction.Wait(() =>
		{
			return roadData.junctionDatas == null || roadData.junctionDatas.Count == 0;
		}, () =>
		{
			junctionPos.Clear();
			foreach (var data in roadData.junctionDatas)
			{
				junctionPos.Add(new Vector3(data.position[0], 0, data.position[1]));
			}
		}));

		StartCoroutine(SendVehicleDataRoutine());
	}
	private void Create()
	{
		if (vehicle == null)
		{
			int index = Random.Range(0, junctionPos.Count);
			vehicle = Instantiate(prefab, junctionPos[index], Quaternion.identity);
			vehicle.transform.SetParent(transform);
			if (vehicle.TryGetComponent<Trafficer>(out var trafficer))
			{
				trafficer.SetDestination(junctionPos[index]);
			}
			vehicle.transform.position = junctionPos[index];
			stateText.text = "Hủy xe Unity";
			Debug.Log("Vehicle created at " + junctionPos[index]);
		}
		else
		{
			Debug.Log("Vehicle already exists");
		}
	}
	private void Destroy()
	{
		if (vehicle != null)
		{
			vehicle.SetIsExist(false);
			vehicleSender.SendUnityData(vehicle.GetUnityVehicleData());
			vehicle = null;
			stateText.text = CMD_CREATE;
		}
		else
		{
			Debug.Log("Vehicle does not exist");
		}
	}

	private IEnumerator SendVehicleDataRoutine() 
	{
		var wait = new WaitForSeconds(0.1f);
		while (true) 
		{
			if (vehicle != null)
			{
				vehicleSender.SendUnityData(vehicle.GetUnityVehicleData());
			}
			yield return wait;
		}
	}
}
