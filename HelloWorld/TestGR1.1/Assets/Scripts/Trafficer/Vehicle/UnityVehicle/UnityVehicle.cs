using UnityEngine;
using System.Collections.Generic;

public class UnityVehicle : Vehicle
{
    private static int idCounter = 0;
	private const string ID_PREFIX = "UnityVehicle_";
	[SerializeField] private float speedMultiplier = 1;

	[SerializeField] private List<Sensor> forwardSensor;
	[SerializeField] private List<Sensor> leftSensor;
	[SerializeField] private List<Sensor> rightSensor;
	[SerializeField] private List<Sensor> backSensor;
	private Vector3 moving;

	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		speed = 10;
        SetId( $"{ID_PREFIX} {idCounter}" );
        VehicleManager.Instance.AddVehicle(this);
		idCounter++;
		lastPos = transform.position;
	}

    // Update is called once per frame
    void Update()
    {
        if (CameraController.Instance.CurrentTrafficer == this)
		{
			Move();
		}
	}
	protected override void Move()
	{
		InvokeMove();
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
		if (Mathf.Abs(moving.z) >= 0.01f)
		{
			float multiplier = 1.5f;
			transform.position += moving.z * speed * speedMultiplier * Time.deltaTime * transform.forward;
			transform.forward = Vector3.Slerp(transform.forward, moving.x * transform.right, Time.deltaTime * multiplier);
		}
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
	public UnityVehicleData GetVehicleData()
	{
		float[] position = { transform.position.x, transform.position.z };
		float[] forward = { transform.forward.x, transform.forward.z };
		bool turnLeft = moving.x > 0;
		bool turnRight = moving.x < 0;
		bool isBraking = moving.z <= 0;
		return new UnityVehicleData(
			GetId(),
			"vehicle",
			position,
			forward,
			speed,
			"E1",
			turnLeft,
			turnRight,
			isBraking,
			isExist
		);
	}
}
