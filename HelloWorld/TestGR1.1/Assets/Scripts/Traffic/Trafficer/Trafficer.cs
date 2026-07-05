using UnityEngine;
using System;

public class Trafficer : MonoBehaviour
{
	public enum InterpolationPositionType
	{
		Linear,
		SLerp, 
		Overwrite
	}
	public enum InterpolationRotationType
	{
		Overwrite,
		Slerp
	}
	[SerializeField] private InterpolationPositionType interpolationPositionType = InterpolationPositionType.Linear;
	[SerializeField] private InterpolationRotationType interpolationRotationType = InterpolationRotationType.Slerp;
	
	private string id = "";
	protected Vector3 destination;
	private Vector3 nextForward;
	protected float speed;


	[SerializeField] private Transform cameraHolder;
	[SerializeField] private float rotateMultiplier = 5f;
	[SerializeField] private bool moveByServer = true;

	public ExistState existState = ExistState.ServerControlled;
	// Cờ quét mỗi packet trong TrafficerManager.ProcessData — xe không thấy trong packet bị recycle.
	// Runtime-only, không serialize.
	[System.NonSerialized] public bool seenThisFrame = true;
	// Xe người chơi sinh từ máy khách (CLIENT_CAR): không pool, hủy hẳn khi recycle.
	[System.NonSerialized] public bool isStandaloneClient = false;

	// Xe đang do client sở hữu (đang lái hoặc xác xe) — server không can thiệp vị trí/ vòng đời.
	public bool IsClientOwned => existState == ExistState.ClientControlled || existState == ExistState.Wrecked;

	protected virtual void Update()
	{
		if (existState == ExistState.ServerControlled && moveByServer)
		{
			Move();
		}
	}

	public virtual void Move()
	{
		float speedMultiplier = SpeedMultiplier.Instance == null ? 1 : SpeedMultiplier.Instance.Multiplier;

		// Interpolate position
		switch (interpolationPositionType)
		{
			case InterpolationPositionType.Linear:
				transform.position = Vector3.MoveTowards(transform.position, destination, speed * speedMultiplier * Time.deltaTime);
				break;
			case InterpolationPositionType.SLerp:
				transform.position = Vector3.Slerp(transform.position, destination, speed * speedMultiplier * Time.deltaTime);
				break;
		}
		if ((transform.position - destination).magnitude < 0.1f)
		{
			transform.position = destination;
		}

		// Interpolate rotation
		switch (interpolationRotationType)		{
			case InterpolationRotationType.Overwrite:
				if (nextForward.magnitude > 0.01f)
				{
					transform.forward = nextForward;
				}
				break;
			case InterpolationRotationType.Slerp:
				transform.forward = Vector3.Slerp(transform.forward, nextForward, rotateMultiplier * Time.deltaTime);
				break;
		}

		if ((transform.position - destination).magnitude > 0.1f && speed <= 0.1f) // position error
		{
			float errorSpeed = 15f; // m/s
			float lerpFactor = errorSpeed * Time.deltaTime * 1/speedMultiplier;
			transform.position = Vector3.Slerp(transform.position, destination, lerpFactor);
		}
	}
	public void Hide()
	{
		gameObject.SetActive(false);
	}

	public void Show()
	{
		gameObject.SetActive(true);
		// Xe client sở hữu (đang lái / xác xe) lấy vị trí từ vật lý, không snap về server.
		if (!IsClientOwned) transform.position = destination;
	}
	public event EventHandler OnDestinationChanged;

	public void SetDestination(Vector3 destination)
	{
		this.destination = destination;
		OnDestinationChanged?.Invoke(this, EventArgs.Empty);
	}
	public Vector3 GetDestination()
	{
		return destination;
	}

	public bool IsReachedDestination()
	{
		return (transform.position - destination).magnitude < 0.1f;
	}

	public void SetSpeed(float speed)
	{
		this.speed = speed;
	}
	public float GetSpeed()
	{
		return speed;
	}
	public void SetId(string id)
	{
		this.id = id;
	}

	public string GetId()
	{
		return id;
	}
	public void SetNextForward(Vector3 forward)
	{
		this.nextForward = forward;
	}
	public Vector3 GetNextForward()
	{
		return nextForward;
	}

	public virtual void ResetFromPool()
	{
		existState = ExistState.ServerControlled;
		seenThisFrame = true;
		isStandaloneClient = false;
	}

	public void Set(TrafficerData trafficerData)
	{
		SetId(trafficerData.id);
		SetDestination(Converter.ToVector3(trafficerData.position));
		SetSpeed(trafficerData.speed);
		// Forward giữ swap thủ công: SUMO emit forward = [cos(angle_rad), sin(angle_rad)]
		// với angle theo convention compass (0° = bắc = +y SUMO). Cần forward[1] → Unity z.
		SetNextForward(new Vector3(trafficerData.forward[1], 0, trafficerData.forward[0]));
	}

	public Transform GetCameraHolder()
	{
		return cameraHolder;
	}
	public float GetFullSpeed()
	{
		return speed * SpeedMultiplier.Instance.Multiplier;
	}
	public float GetBaseSpeed()
	{
		return speed;
	}

	protected virtual void OnDisable()
	{
		CameraController cmC = cameraHolder.GetComponentInChildren<CameraController>();
		if (cmC != null)
		{
			cmC.SetRandomTrafficerView();
		}
	}
	protected virtual void OnEnable() {
		// Khi bị cull theo khoảng cách rồi hiện lại: xe client-owned giữ vị trí vật lý, không snap về server.
		if (!IsClientOwned) transform.position = destination;
	}
	
}
