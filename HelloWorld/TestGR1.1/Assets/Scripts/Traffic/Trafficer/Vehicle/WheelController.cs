using UnityEngine;

/// <summary>
/// Điều khiển 4 WheelCollider của một xe: ga, lái, phanh, đồng bộ pose bánh hiển thị,
/// và bật/tắt vật lý bánh. Hoàn toàn độc lập với logic state/điều khiển của xe —
/// nhận input dưới dạng tham số, ai cần thì gọi các hàm public.
///
/// Tuning cảm giác lái (game lái xe thực thụ):
///   - Phanh dễ hơn        → brakeForce lớn + forward friction stiffness cao.
///   - Rẽ dễ hơn           → maxSteerAngle vừa phải + giảm góc lái theo tốc độ + làm mượt lái.
///   - Ít trượt khi nhả ga / trả lái → sideways friction stiffness cao + hãm động cơ (engine braking).
/// </summary>
[RequireComponent(typeof(Rigidbody))]
public class WheelController : MonoBehaviour
{
	[Header("Motor Settings")]
	[Tooltip("Mô-men kéo tối đa của động cơ (Nm). Tăng để tăng tốc nhanh hơn.")]
	[SerializeField] private float motorForce = 1500f;
	[Tooltip("Mô-men phanh khi đạp phanh/handbrake (Nm). Tăng để xe DỄ PHANH hơn.")]
	[SerializeField] private float brakeForce = 5000f;
	[Tooltip("Mô-men hãm khi nhả ga (engine braking). Giúp xe giảm tốc tự nhiên, ÍT TRƯỢT theo quán tính.")]
	[SerializeField] private float engineBrakeForce = 800f;

	[Header("Steering")]
	[Tooltip("Góc lái tối đa ở tốc độ thấp (độ). Tăng để xe DỄ RẼ hơn khi chạy chậm/đỗ.")]
	[SerializeField] private float maxSteerAngle = 35f;
	[Tooltip("Góc lái tối thiểu ở tốc độ cao (độ). Nhỏ hơn maxSteerAngle để tránh giật lái/lật ở tốc độ cao.")]
	[SerializeField] private float minSteerAngle = 24f;
	[Tooltip("Tốc độ (m/s) mà tại đó góc lái đã giảm về minSteerAngle.")]
	[SerializeField] private float fullSteerReductionSpeed = 25f;
	[Tooltip("Tốc độ nội suy góc lái (đánh + trả lái). Lớn = lái nhạy; nhỏ = mượt, trả lái êm hơn.")]
	[SerializeField] private float steerLerpSpeed = 8f;

	[Header("Grip — Forward friction (dọc: kéo/phanh)")]
	[Tooltip("Độ bám dọc. Stiffness cao → tăng tốc & phanh ăn hơn, ít trượt bánh khi tăng/giảm ga.")]
	[SerializeField] private float forwardStiffness = 1.6f;
	[SerializeField] private float forwardExtremumSlip = 0.4f;
	[SerializeField] private float forwardExtremumValue = 1.0f;
	[SerializeField] private float forwardAsymptoteSlip = 0.8f;
	[SerializeField] private float forwardAsymptoteValue = 0.6f;

	[Header("Grip — Sideways friction (ngang: chống trượt khi rẽ)")]
	[Tooltip("Độ bám ngang. Stiffness CAO là yếu tố chính giúp xe ÍT TRƯỢT khi rẽ / trả lái / nhả ga.")]
	[SerializeField] private float sidewaysStiffness = 2.4f;
	[SerializeField] private float sidewaysExtremumSlip = 0.2f;
	[SerializeField] private float sidewaysExtremumValue = 1.0f;
	[SerializeField] private float sidewaysAsymptoteSlip = 0.5f;
	[SerializeField] private float sidewaysAsymptoteValue = 0.8f;

	[Header("Stability")]
	[Tooltip("Độ lệch trọng tâm theo trục Y (mét, âm = hạ thấp). Hạ trọng tâm → bớt lật, vào cua đầm hơn.")]
	[SerializeField] private float centerOfMassYOffset = -0.6f;
	[Tooltip("Cản góc (angular drag) của Rigidbody. Cao hơn → xe bớt xoay/đảo lái khi mất bám.")]
	[SerializeField] private float angularDrag = 2.5f;
	[Tooltip("Độ cứng thanh cân bằng (anti-roll bar). CAO → thân xe ÍT NGHIÊNG khi vào cua. " +
	         "Quá cao có thể làm xe nảy/cứng. Đặt 0 để tắt.")]
	[SerializeField] private float antiRollForce = 6000f;

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

	private Rigidbody rb;
	private float currentSteerAngle; // góc lái đã nội suy (để trả lái mượt)
	private bool handBraking;        // người chơi đang giữ phanh

	private void Awake()
	{
		rb = GetComponent<Rigidbody>();
		ApplyTuning();
	}

	// Áp friction curve + cản góc. KHÔNG đụng centerOfMass ở đây — xem ApplyCenterOfMass.
	private void ApplyTuning()
	{
		if (rb != null) rb.angularDamping = angularDrag;
		ApplyFriction(frontLeftWc);
		ApplyFriction(frontRightWc);
		ApplyFriction(rearLeftWc);
		ApplyFriction(rearRightWc);
	}

	/// <summary>
	/// Đặt lại trọng tâm một cách TẤT ĐỊNH. Phải gọi khi wheel collider ĐANG BẬT (chế độ vật lý),
	/// để CoM tự-tính của Unity bao gồm cả bánh — giống nhau cho xe client-sinh lẫn xe server bị chiếm.
	/// Nếu gọi lúc bánh tắt (xe server kinematic), CoM tính thiếu bánh → lệch → xe vẹo/khó lái.
	/// </summary>
	public void ApplyCenterOfMass()
	{
		if (rb == null) rb = GetComponent<Rigidbody>(); // phòng khi gọi trước WheelController.Awake
		if (rb == null) return;
		rb.ResetCenterOfMass(); // về CoM tự-tính theo các collider hiện đang bật
		rb.centerOfMass += new Vector3(0f, centerOfMassYOffset, 0f);
	}

	private void ApplyFriction(WheelCollider wc)
	{
		if (wc == null) return;

		WheelFrictionCurve fwd = wc.forwardFriction;
		fwd.extremumSlip = forwardExtremumSlip;
		fwd.extremumValue = forwardExtremumValue;
		fwd.asymptoteSlip = forwardAsymptoteSlip;
		fwd.asymptoteValue = forwardAsymptoteValue;
		fwd.stiffness = forwardStiffness;
		wc.forwardFriction = fwd;

		WheelFrictionCurve side = wc.sidewaysFriction;
		side.extremumSlip = sidewaysExtremumSlip;
		side.extremumValue = sidewaysExtremumValue;
		side.asymptoteSlip = sidewaysAsymptoteSlip;
		side.asymptoteValue = sidewaysAsymptoteValue;
		side.stiffness = sidewaysStiffness;
		wc.sidewaysFriction = side;
	}

	// Anti-roll bar: cân lực giữa 2 bánh cùng trục theo độ nén hệ treo → giữ thân xe phẳng khi cua.
	// Chỉ chạy khi bánh đang bật vật lý (xe client/wreck); xe server kinematic bỏ qua.
	private void FixedUpdate()
	{
		if (antiRollForce <= 0f || frontLeftWc == null || !frontLeftWc.enabled || rb == null) return;
		ApplyAntiRoll(frontLeftWc, frontRightWc);
		ApplyAntiRoll(rearLeftWc, rearRightWc);
	}

	private void ApplyAntiRoll(WheelCollider left, WheelCollider right)
	{
		if (left == null || right == null) return;

		// travel = mức duỗi hệ treo (0 = nén hết, 1 = duỗi hết). Bánh không chạm đất coi như duỗi hết.
		float travelL = 1f, travelR = 1f;
		bool groundedL = left.GetGroundHit(out WheelHit hitL);
		if (groundedL)
			travelL = (-left.transform.InverseTransformPoint(hitL.point).y - left.radius) / left.suspensionDistance;
		bool groundedR = right.GetGroundHit(out WheelHit hitR);
		if (groundedR)
			travelR = (-right.transform.InverseTransformPoint(hitR.point).y - right.radius) / right.suspensionDistance;

		// Bánh nén nhiều hơn (travel nhỏ) bị đẩy xuống, bánh kia kéo lên → triệt nghiêng thân.
		float antiRoll = (travelL - travelR) * antiRollForce;
		if (groundedL)
			rb.AddForceAtPosition(left.transform.up * -antiRoll, left.transform.position);
		if (groundedR)
			rb.AddForceAtPosition(right.transform.up * antiRoll, right.transform.position);
	}

	/// <summary>Bật/tắt vật lý 4 bánh (dùng cho chế độ hybrid).</summary>
	public void SetCollidersEnabled(bool on)
	{
		if (frontLeftWc != null) frontLeftWc.enabled = on;
		if (frontRightWc != null) frontRightWc.enabled = on;
		if (rearLeftWc != null) rearLeftWc.enabled = on;
		if (rearRightWc != null) rearRightWc.enabled = on;
	}

	/// <summary>Ga theo input dọc (>0 tiến, &lt;0 lùi, ~0 nhả). Nhả ga → hãm động cơ để bớt trôi.</summary>
	public void Drive(float forwardInput)
	{
		bool throttling = Mathf.Abs(forwardInput) > 0.01f;
		float torque = throttling ? motorForce * forwardInput : 0f;
		frontLeftWc.motorTorque = torque;
		frontRightWc.motorTorque = torque;
		rearLeftWc.motorTorque = torque;
		rearRightWc.motorTorque = torque;

		// Phanh ưu tiên: handbrake > hãm động cơ (khi đang coasting) > 0.
		float brakeTorque = handBraking ? brakeForce : (throttling ? 0f : engineBrakeForce);
		ApplyBrakeTorque(brakeTorque);
	}

	/// <summary>Lái theo input ngang. Góc lái giảm theo tốc độ + nội suy để đánh/trả lái mượt.</summary>
	public void Steer(float steerInput)
	{
		float speed = rb != null ? rb.linearVelocity.magnitude : 0f;
		float t = fullSteerReductionSpeed > 0.01f ? Mathf.Clamp01(speed / fullSteerReductionSpeed) : 0f;
		float speedAdjustedMax = Mathf.Lerp(maxSteerAngle, minSteerAngle, t);

		float targetAngle = speedAdjustedMax * steerInput;
		currentSteerAngle = Mathf.Lerp(currentSteerAngle, targetAngle, Time.deltaTime * steerLerpSpeed);

		frontLeftWc.steerAngle = currentSteerAngle;
		frontRightWc.steerAngle = currentSteerAngle;
	}

	/// <summary>Phanh (true) / nhả phanh (false). Lưu trạng thái; lực thực áp ở Drive().</summary>
	public void Brake(bool isBraking)
	{
		handBraking = isBraking;
		if (isBraking) ApplyBrakeTorque(brakeForce);
	}

	private void ApplyBrakeTorque(float torque)
	{
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
