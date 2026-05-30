using UnityEngine;
using System.Collections.Generic;
using System;

[RequireComponent(typeof(Trafficer))]
public class UnityVehicle : MonoBehaviour
{
	private Trafficer trafficer;

    private static int idCounter = 0;
	private const string ID_PREFIX = "UnityVehicle_";
	[SerializeField] private float speedMultiplier = 1;
	[SerializeField] private float speed = 14;
	[SerializeField] private float rotateMultiplier = 5f;

	[Header("Sensors")]
	[SerializeField] private List<Sensor> forwardSensor;
	[SerializeField] private List<Sensor> leftSensor;
	[SerializeField] private List<Sensor> rightSensor;
	[SerializeField] private List<Sensor> backSensor;

	[Header("Motor Settings")]
	[SerializeField] private float motorForce = 1500f;
	[SerializeField] private float brakeForce = 3000f;
	[SerializeField] private float maxSteerAngle = 30f;

	[Header("Wheel Colliders")]
	[SerializeField] private WheelCollider frontLeftWc;
	[SerializeField] private WheelCollider frontRightWc;
	[SerializeField] private WheelCollider rearLeftWc;
	[SerializeField] private WheelCollider rearRightWc;

	[Header("Wheel Transforms")]
	[SerializeField] private Transform frontLeftWheel;
	[SerializeField] private Transform frontRightWheel;
	[SerializeField] private Transform rearLeftWheel;
	[SerializeField] private Transform rearRightWheel;

	[Header("DevMode")]
	[SerializeField] private bool devMode = false;

	private Vector3 moving;

	private void Awake()
	{
		if (!devMode)
		{
			trafficer = GetComponent<Trafficer>();
		}
		
	}

	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		GameInput.Instance.OnBrakePressed += OnBrakePressed;
		GameInput.Instance.OnBrakeReleased += OnBrakeReleased;
		if (devMode) return;
		trafficer.SetSpeed(speed);
        trafficer.SetId( $"{ID_PREFIX} {idCounter}" );
        TrafficerManager.Instance.AddTrafficer(trafficer);
		idCounter++;
		trafficer.SetDestination(transform.position);
		
	}

    private void OnBrakeReleased(object sender, EventArgs e)
    {
		ApplyBrakes(false);
    }

    private void OnBrakePressed(object sender, EventArgs e)
	{
		ApplyBrakes(true);
	}
	

    // Update is called once per frame
    void FixedUpdate()
    {
		if (!devMode)
		{
			if (CameraController.Instance != null && CameraController.Instance.CurrentTrafficer == trafficer)
			{
				HandleMotor();
				HandleSteering();
				UpdateWheelPoses();
			}

		}
		else
		{
			HandleMotor();
			HandleSteering();
			UpdateWheelPoses();
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
			nextPosition += moving.z * trafficer.GetSpeed() * speedMultiplier * Time.deltaTime * transform.forward;
			trafficer.SetNextForward(Vector3.Slerp(trafficer.GetNextForward(), moving.x * transform.right, Time.deltaTime * rotateMultiplier));
		}
		// Debug.Log($"Moving: {moving}, Next Position: {nextPosition}, Speed: {trafficer.GetSpeed()}");
		return nextPosition;
	}

	private void HandleMotor()
	{
		// Debug.Log("handle motor	");
		Vector3 input = GameInput.Instance.GetMovementInput();
		if (Mathf.Abs(input.z) > 0.01f)
		{
			// Debug.Log($"Input: {input}, Moving: {moving}");
			frontLeftWc.motorTorque = motorForce * input.z;
			frontRightWc.motorTorque = motorForce * input.z;
			rearLeftWc.motorTorque = motorForce * input.z;
			rearRightWc.motorTorque = motorForce * input.z;
		}
		else
		{
			frontLeftWc.motorTorque = 0;
			frontRightWc.motorTorque = 0;
			rearLeftWc.motorTorque = 0;
			rearRightWc.motorTorque = 0;
		}
	}
	private void HandleSteering()
	{
		Vector3 input = GameInput.Instance.GetMovementInput();
		float steerAngle = maxSteerAngle * input.x;
		frontLeftWc.steerAngle = steerAngle;
		frontRightWc.steerAngle = steerAngle;
	}
	private void ApplyBrakes(bool isBraking)
	{
		// Debug.Log($"Applying Brakes: {isBraking}");
		if (isBraking)
		{
			frontLeftWc.brakeTorque = brakeForce;
			frontRightWc.brakeTorque = brakeForce;
			rearLeftWc.brakeTorque = brakeForce;
			rearRightWc.brakeTorque = brakeForce;
			// Debug.Log("Braking");
		}
		else
		{
			frontLeftWc.brakeTorque = 0;
			frontRightWc.brakeTorque = 0;
			rearLeftWc.brakeTorque = 0;
			rearRightWc.brakeTorque = 0;
			// Debug.Log("Released Brakes");
		}
	}
	private void UpdateWheelPoses()
	{
		UpdateWheelPose(frontLeftWc, frontLeftWheel);
		UpdateWheelPose(frontRightWc, frontRightWheel);
		UpdateWheelPose(rearLeftWc, rearLeftWheel);
		UpdateWheelPose(rearRightWc, rearRightWheel);
	}
	private void UpdateWheelPose(WheelCollider wc, Transform wheel)
	{
        wc.GetWorldPose(out Vector3 pos, out Quaternion rot);
        wheel.SetPositionAndRotation(pos, rot);
    }
	private bool CanMoveForward()
	{
		if (devMode) return true;
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
		if (devMode) return true;
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
		if (devMode) return true;
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
		if (devMode) return true;
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
