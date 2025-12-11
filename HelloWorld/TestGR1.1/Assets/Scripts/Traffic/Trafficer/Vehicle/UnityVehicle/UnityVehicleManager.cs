using UnityEngine;
using UnityEngine.UI;
using TMPro;
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
	private List<Vector3> junctionPos = new List<Vector3>();

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
	}
	private void Create()
	{
		if (vehicle == null)
		{
			int index = Random.Range(0, junctionPos.Count);
			GameObject vehicle = Instantiate(prefab.gameObject, junctionPos[index], Quaternion.identity);
			StartCoroutine(ManipulateAction.Delay(() =>
			{
				this.vehicle = vehicle.GetComponent<UnityVehicle>();
			}, Time.deltaTime));
			vehicle.transform.SetParent(transform);
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
			vehicle.isExist = false;
			vehicle = null;
			stateText.text = CMD_CREATE;
		}
		else
		{
			Debug.Log("Vehicle does not exist");
		}
	}
	private void FixedUpdate() {
		vehicleSender.SendUnityData(vehicle?.GetVehicleData());
	}
}
