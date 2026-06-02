using UnityEngine;

/// <summary>
/// Điều khiển 4 WheelCollider của một xe: ga, lái, phanh, đồng bộ pose bánh hiển thị,
/// và bật/tắt vật lý bánh. Hoàn toàn độc lập với logic state/điều khiển của xe —
/// nhận input dưới dạng tham số, ai cần thì gọi các hàm public.
/// </summary>
public class WheelController : MonoBehaviour
{
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

	/// <summary>Bật/tắt vật lý 4 bánh (dùng cho chế độ hybrid).</summary>
	public void SetCollidersEnabled(bool on)
	{
		if (frontLeftWc != null) frontLeftWc.enabled = on;
		if (frontRightWc != null) frontRightWc.enabled = on;
		if (rearLeftWc != null) rearLeftWc.enabled = on;
		if (rearRightWc != null) rearRightWc.enabled = on;
	}

	/// <summary>Ga theo input dọc (>0 tiến, &lt;0 lùi, ~0 nhả).</summary>
	public void Drive(float forwardInput)
	{
		float torque = Mathf.Abs(forwardInput) > 0.01f ? motorForce * forwardInput : 0f;
		frontLeftWc.motorTorque = torque;
		frontRightWc.motorTorque = torque;
		rearLeftWc.motorTorque = torque;
		rearRightWc.motorTorque = torque;
	}

	/// <summary>Lái theo input ngang.</summary>
	public void Steer(float steerInput)
	{
		float steerAngle = maxSteerAngle * steerInput;
		frontLeftWc.steerAngle = steerAngle;
		frontRightWc.steerAngle = steerAngle;
	}

	/// <summary>Phanh (true) / nhả phanh (false).</summary>
	public void Brake(bool isBraking)
	{
		Debug.Log($"WheelController: Brake({isBraking})");
		float torque = isBraking ? brakeForce : 0f;
		frontLeftWc.brakeTorque = torque;
		frontRightWc.brakeTorque = torque;
		rearLeftWc.brakeTorque = torque;
		rearRightWc.brakeTorque = torque;
	}

	/// <summary>Đồng bộ transform bánh hiển thị theo trạng thái WheelCollider.</summary>
	public void UpdatePoses()
	{
		UpdatePose(frontLeftWc, frontLeftWheel);
		UpdatePose(frontRightWc, frontRightWheel);
		UpdatePose(rearLeftWc, rearLeftWheel);
		UpdatePose(rearRightWc, rearRightWheel);
	}

	private void UpdatePose(WheelCollider wc, Transform wheel)
	{
		wc.GetWorldPose(out Vector3 pos, out Quaternion rot);
		wheel.SetPositionAndRotation(pos, rot);
	}
}
