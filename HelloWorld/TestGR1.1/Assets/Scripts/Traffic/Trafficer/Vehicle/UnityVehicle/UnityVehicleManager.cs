using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;
using System.Collections.Generic;
using UnityEngine.SceneManagement;

public class UnityVehicleManager : MonoBehaviour
{
	public static UnityVehicleManager Instance { get; private set; }

	private const string CMD_CREATE = "Tạo xe Unity";
	private const string CLIENT_CAR_ID = "CLIENT_CAR";  // id đặc biệt, duy nhất, server không chiếm quyền
	private const string GENERIC_LANE = "generic";
	private const float SPAWN_FORWARD_OFFSET = 5f;       // cách điểm đầu lane 5m về phía trước
	private const int PRE_RENDER_SCENE_INDEX = 2;

	// Chunk 5: one-shot release signal — drain mỗi batch, gửi state=1 cho server re-anchor.
	private List<UnityVehicleData> pendingReleaseItems = new List<UnityVehicleData>();

	private UnityVehicle vehicle = null;
    [SerializeField] private Button stateButton;
	[SerializeField] private TMP_Text stateText;
    [SerializeField] private UnityVehicle prefab;
	[SerializeField] private VehicleSender vehicleSender;
	[SerializeField] private RoadDataSO roadData;

	private void Awake()
	{
		Instance = this;
	}

	private void OnDestroy()
	{
		Instance = null;
	}

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

		StartCoroutine(SendVehicleDataRoutine());
	}

	private void Create()
	{
		if (SceneManager.GetActiveScene().buildIndex == PRE_RENDER_SCENE_INDEX) return;
		if (vehicle != null)
		{
			Debug.Log("Vehicle already exists");
			return;
		}
		if (!TryGetNearestLaneSpawn(out Vector3 spawnPos, out Quaternion spawnRot))
		{
			Debug.LogWarning("Không tìm được lane generic phù hợp (segment đầu > 5m) để sinh xe client.");
			return;
		}

		vehicle = Instantiate(prefab, spawnPos, spawnRot);
		vehicle.transform.SetParent(transform);
		vehicle.transform.SetPositionAndRotation(spawnPos, spawnRot);
		if (vehicle.TryGetComponent<Trafficer>(out var trafficer))
		{
			// UnityVehicle.Start không còn tự đăng ký — manager gán danh tính tại đây.
			trafficer.SetId(CLIENT_CAR_ID);
			trafficer.isStandaloneClient = true;
			trafficer.SetDestination(spawnPos);
			TrafficerManager.Instance.AddTrafficer(trafficer);
		}
		vehicle.TakeControl();  // ClientControlled + bật vật lý/input
		stateText.text = "Hủy xe Unity";
		Debug.Log("Client car spawned on lane at " + spawnPos);
	}

	// Tìm edge có lane generic đầu tiên gần camera nhất với segment đầu dài hơn 5m;
	// trả về vị trí cách điểm đầu lane 5m về phía trước, quay theo hướng lane.
	private bool TryGetNearestLaneSpawn(out Vector3 position, out Quaternion rotation)
	{
		position = Vector3.zero;
		rotation = Quaternion.identity;
		if (roadData == null || roadData.edgeDatas == null || roadData.edgeDatas.Count == 0)
			return false;

		Vector3 camPos = CameraController.Instance != null
			? CameraController.Instance.transform.position
			: (Camera.main != null ? Camera.main.transform.position : Vector3.zero);

		EdgeData bestEdge = null;
		float bestDist = float.MaxValue;

		foreach (EdgeData edge in roadData.edgeDatas)
		{
			Lane lane = FirstGenericLane(edge);
			if (lane == null || lane.points == null || lane.points.Count < 2) continue;

			Vector3 start = Converter.ToVector3(lane.points[0]);
			Vector3 next = Converter.ToVector3(lane.points[1]);
			if ((next - start).magnitude <= SPAWN_FORWARD_OFFSET) continue;

			float dist = Vector3.Distance(camPos, start);
			if (dist < bestDist)
			{
				bestDist = dist;
				bestEdge = edge;
			}
		}

		if (bestEdge == null) return false;

		Lane bestLane = FirstGenericLane(bestEdge);
		Vector3 s = Converter.ToVector3(bestLane.points[0]);
		Vector3 n = Converter.ToVector3(bestLane.points[1]);
		Vector3 dir = (n - s).normalized;
		position = s + dir * SPAWN_FORWARD_OFFSET;
		rotation = Quaternion.LookRotation(dir);
		return true;
	}

	private static Lane FirstGenericLane(EdgeData edge)
	{
		if (edge == null || edge.lanes == null) return null;
		foreach (Lane lane in edge.lanes)
		{
			if (lane.type == GENERIC_LANE) return lane;
		}
		return null;
	}

	private void Destroy()
	{
		if (vehicle != null)
		{
			if (vehicle.TryGetComponent<Trafficer>(out var trafficer))
				TrafficerManager.Instance.RemoveTrafficer(trafficer);
			Destroy(vehicle.gameObject);
			vehicle = null;
			stateText.text = CMD_CREATE;
		}
		else
		{
			Debug.Log("Vehicle does not exist");
		}
	}

	/// <summary>Đăng ký one-shot tín hiệu thả quyền (state=1) để gửi cùng batch tiếp theo.</summary>
	public void EnqueueRelease(UnityVehicleData data)
	{
		pendingReleaseItems.Add(data);
	}

	private IEnumerator SendVehicleDataRoutine()
	{
		var wait = new WaitForSeconds(0.1f);
		bool hadCars = false;
		while (true)
		{
			// Gom MỌI xe client-owned (CLIENT_CAR + xe server bị chiếm + xác xe) thành 1 batch / 1 message.
			if (TrafficerManager.Instance != null)
			{
				List<UnityVehicleData> batch = new List<UnityVehicleData>();

				// Chunk 5: drain pending release signals (one-shot, state=1 — re-anchor).
				if (pendingReleaseItems.Count > 0)
				{
					batch.AddRange(pendingReleaseItems);
					pendingReleaseItems.Clear();
				}

				foreach (Trafficer t in TrafficerManager.Instance.GetTrafficers())
				{
					if (!t.IsClientOwned) continue;
					if (t.TryGetComponent<UnityVehicle>(out var uv))
					{
						batch.Add(uv.GetUnityVehicleData());
					}
				}

				if (batch.Count > 0)
				{
					vehicleSender.SendBatch(batch);
					hadCars = true;
				}
				else if (hadCars)
				{
					// Vừa hết xe client → gửi 1 batch rỗng để server reconcile xoá xe cuối, rồi im lặng.
					vehicleSender.SendBatch(batch);
					hadCars = false;
				}
			}
			yield return wait;
		}
	}
}
