using UnityEngine;

public abstract class Trafficer : MonoBehaviour
{
	private string id = "";
	protected Vector3 destination;
	protected float speed;
	private Vector3 lastPosition;

	[SerializeField] private Transform cameraHolder;

	public bool isExist = true;


	protected virtual void Move()
	{
		lastPosition = transform.position;
		float speedMultiplier = SpeedMultiplier.Instance.Multiplier;
		//transform.position = Vector3.Lerp(transform.position, destination, speed * speedMultiplier * Time.deltaTime);
		transform.position = Vector3.MoveTowards(transform.position, destination, speed * speedMultiplier * Time.deltaTime);
		if ((transform.position - destination).magnitude < 0.1f)
		{
			transform.position = destination;
		}
		Vector3 direction = transform.position - lastPosition;
		if (direction != Vector3.zero)
		{
			float multiplier = 5;
			transform.forward = Vector3.Slerp(transform.forward, direction, speed * Time.deltaTime * multiplier);
		}
		if ((transform.position - destination).magnitude > 0.1f && speed == 0) // position error
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

	public void SetSpeed(float speed)
	{
		this.speed = speed;
	}
	public void SetId(string id)
	{
		this.id = id;
	}

	public string GetId()
	{
		return id;
	}

	public void Set(TrafficerData trafficerData)
	{
		SetId(trafficerData.id);
		SetDestination(Converter.ToVector3(trafficerData.position));
		SetSpeed(trafficerData.speed);
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
	
}
