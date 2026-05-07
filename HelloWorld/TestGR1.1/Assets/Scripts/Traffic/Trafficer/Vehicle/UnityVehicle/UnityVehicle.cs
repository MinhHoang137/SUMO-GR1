using UnityEngine;
using System.Collections.Generic;

[RequireComponent(typeof(Trafficer))]
public class UnityVehicle : MonoBehaviour
{
	private Trafficer trafficer;

    private static int idCounter = 0;
	private const string ID_PREFIX = "UnityVehicle_";
	[SerializeField] private float speedMultiplier = 1;
	[SerializeField] private float speed = 14;

	[SerializeField] private List<Sensor> forwardSensor;
	[SerializeField] private List<Sensor> leftSensor;
	[SerializeField] private List<Sensor> rightSensor;
	[SerializeField] private List<Sensor> backSensor;
	private Vector3 moving;

	private void Awake()
	{
		trafficer = GetComponent<Trafficer>();
	}

	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		trafficer.SetRotateBySelf(false);
		trafficer.SetSpeed(speed);
        trafficer.SetId( $"{ID_PREFIX} {idCounter}" );
        TrafficerManager.Instance.AddTrafficer(trafficer);
		idCounter++;
		trafficer.SetDestination(transform.position);
	}

    // Update is called once per frame
    void Update()
    {
        if (CameraController.Instance.CurrentTrafficer == trafficer)
		{
			trafficer.SetDestination(CustomMove());
		}
		else
		{
			trafficer.SetDestination(transform.position);
		}
	}
	private Vector3 CustomMove()
	{
		Vector3 input = GameInput.Instance.GetMovementInput();
		moving = Vector3.zero;
		if (input.z > 0.01f && CanMoveForward())
		{
			moving = new Vector3(moving.x, 0, input.z);
		}
		if (input.x > 0.01f && CanMoveRight())
		{
			moving = new Vector3(input.x, 0, moving.z);
		}
		if (input.x < -0.01f && CanMoveLeft())
		{
			moving = new Vector3(input.x, 0, moving.z);
		}
		if (input.z < -0.01f && CanMoveBack())
		{
			moving = new Vector3(moving.x, 0, input.z);
		}
		Vector3 nextPosition = transform.position;
		if (Mathf.Abs(moving.z) >= 0.01f)
		{
			float multiplier = 1.5f;
			nextPosition += moving.z * trafficer.GetSpeed() * speedMultiplier * Time.deltaTime * transform.forward;
			transform.forward = Vector3.Slerp(transform.forward, moving.x * transform.right, Time.deltaTime * multiplier);
		}
		// Debug.Log($"Moving: {moving}, Next Position: {nextPosition}, Speed: {trafficer.GetSpeed()}");
		return nextPosition;
	}
	private bool CanMoveForward()
	{
		foreach (Sensor sensor in forwardSensor)
		{
			if (!sensor.CanMove())
			{
				return false;
			}
		}
		return true;
	}
	private bool CanMoveLeft()
	{
		foreach (Sensor sensor in leftSensor)
		{
			if (!sensor.CanMove())
			{
				return false;
			}
		}
		return true;
	}
	private bool CanMoveRight()
	{
		foreach (Sensor sensor in rightSensor)
		{
			if (!sensor.CanMove())
			{
				return false;
			}
		}
		return true;
	}
	private bool CanMoveBack()
	{
		foreach (Sensor sensor in backSensor)
		{
			if (!sensor.CanMove())
			{
				return false;
			}
		}
		return true;
	}
	public void SetIsExist(bool isExist)
	{
		trafficer.isExist = isExist;
	}
	public UnityVehicleData GetUnityVehicleData()
	{
		float[] position = { transform.position.x, transform.position.z };
		float[] forward = { transform.forward.x, transform.forward.z };
		return new UnityVehicleData(
			trafficer.GetId(),
			position,
			forward,
			trafficer.GetSpeed(),
			trafficer.isExist
		);
	}
}
