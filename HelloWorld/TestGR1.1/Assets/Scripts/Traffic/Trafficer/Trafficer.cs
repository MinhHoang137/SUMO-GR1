using UnityEngine;

public class Trafficer : MonoBehaviour
{
	public enum InterpolationPositionType
	{
		Linear,
		SLerp
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

	public bool isExist = true;

	protected virtual void Update()
	{
		Move();
	}

	public virtual void Move()
	{
		float speedMultiplier = SpeedMultiplier.Instance.Multiplier;

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
				transform.forward = nextForward;
				break;
			case InterpolationRotationType.Slerp:
				transform.forward = Vector3.Slerp(transform.forward, nextForward, rotateMultiplier * Time.deltaTime);
				break;
		}

		if ((transform.position - destination).magnitude > 0.1f && speed <= 0.1f) // position error
		{
			transform.position = destination;
		}
	}
	public void Hide()
	{
		gameObject.SetActive(false);
	}

	public void Show()
	{
		gameObject.SetActive(true);
		transform.position = destination;
	}
	public void SetDestination(Vector3 destination)
	{
		this.destination = destination;
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

	public void Set(TrafficerData trafficerData)
	{
		SetId(trafficerData.id);
		SetDestination(new Vector3(trafficerData.position[0], 0, trafficerData.position[1]));
		SetSpeed(trafficerData.speed);
		SetNextForward(new Vector3(trafficerData.forward[1], 0, trafficerData.forward[0]));
	}

	public Transform GetCameraHolder()
	{
		return cameraHolder;
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
		transform.position = destination;
	}
	
}
