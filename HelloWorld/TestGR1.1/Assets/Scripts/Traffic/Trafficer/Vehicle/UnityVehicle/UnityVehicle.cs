using UnityEngine;
using UnityEngine.Events;
using System;

[RequireComponent(typeof(Trafficer))]
[RequireComponent(typeof(WheelController))]
public class UnityVehicle : MonoBehaviour
{
	private Trafficer trafficer;
	private Rigidbody rb;
	private WheelController wheels;
	[SerializeField] private PauseSO pauseSO;

	[Header("DevMode")]
	[SerializeField] private bool devMode = false;

	[Header("Events")]
	// Bắn khi xe trở thành xác xe (sau va chạm) — dùng để bật icon "xe hỏng".
	[SerializeField] private UnityEvent onBecomeWreck;

	public int wreckStartStep;
	private bool hasCrashed;

	private void Awake()
	{
		trafficer = GetComponent<Trafficer>();
		rb = GetComponent<Rigidbody>();
		wheels = GetComponent<WheelController>();
		// Khởi tạo theo state: server → kinematic + tắt wheel collider; client/wreck → bật vật lý.
		ApplyMode(devMode ? ExistState.ClientControlled : trafficer.existState);
	}

	private void OnEnable()
	{
		if (GameInput.Instance != null)
		{
			GameInput.Instance.OnBrakePressed += OnBrakePressed;
			GameInput.Instance.OnBrakeReleased += OnBrakeReleased;
		}
		// Awake không chạy lại khi tái dùng từ pool / hiện lại sau cull → áp lại chế độ theo state đã lưu.
		if (trafficer != null) ApplyMode(devMode ? ExistState.ClientControlled : trafficer.existState);
	}

	private void OnDisable()
	{
		if (GameInput.Instance != null)
		{
			GameInput.Instance.OnBrakePressed -= OnBrakePressed;
			GameInput.Instance.OnBrakeReleased -= OnBrakeReleased;
		}
	}

	// ── Chuyển chế độ điều khiển ─────────────────────────────────────
	/// <summary>Client chiếm quyền lái xe này.</summary>
	public void TakeControl()
	{
		hasCrashed = false;
		trafficer.existState = ExistState.ClientControlled;
		ApplyMode(ExistState.ClientControlled);
		if (TryGetComponent(out Vehicle vehicle))
		{
			vehicle.enabled = false; // tắt logic Vehicle 
		}
	}

	/// <summary>Trả quyền — xe bị hủy ngay (server remove, Unity recycle khi vắng trong stream).</summary>
	public void ReleaseControl()
	{
		if (hasCrashed)
		{
			BecomeWreck();
			return;
		}
		trafficer.existState = ExistState.ServerControlled;
		ApplyMode(ExistState.ServerControlled);
		if (TryGetComponent(out Vehicle vehicle))
		{
			vehicle.enabled = true;
		}
		// Gửi one-shot state=1 → server hủy xe. Không áp dụng cho CLIENT_CAR.
		if (!trafficer.isStandaloneClient && UnityVehicleManager.Instance != null)
			UnityVehicleManager.Instance.EnqueueRelease(GetUnityVehicleData());
	}

	/// <summary>Thành xác xe sau va chạm: vật lý nhưng không ai lái.</summary>
	public void BecomeWreck(Vector3 impulse = default)
	{
		trafficer.existState = ExistState.Wrecked;
		wreckStartStep = TrafficerManager.Instance != null ? TrafficerManager.Instance.CurrentStep : 0;
		ApplyMode(ExistState.Wrecked);
		// ApplyMode đã đặt rb về dynamic → AddForce mới có tác dụng
		if (rb != null && impulse != Vector3.zero)
			rb.AddForce(impulse, ForceMode.Impulse);
		onBecomeWreck?.Invoke();
	}

	// Hybrid: chỉ bật vật lý (Rigidbody dynamic + wheel collider) ở chế độ client/wreck.
	private void ApplyMode(ExistState mode)
	{
		bool physics = mode == ExistState.ClientControlled || mode == ExistState.Wrecked;
		if (rb != null) rb.isKinematic = !physics;
		if (wheels != null)
		{
			wheels.SetCollidersEnabled(physics);
			// Bật vật lý: đặt lại trọng tâm khi bánh đã bật (CoM gồm cả bánh — tất định cho mọi xe),
			// và xoá vận tốc tồn dư từ giai đoạn kinematic để xe không bị giật/vẹo lúc tiếp quản.
			if (physics)
			{
				wheels.ApplyCenterOfMass();
				if (rb != null)
				{
					rb.linearVelocity = Vector3.zero;
					rb.angularVelocity = Vector3.zero;
				}
			}
		}
	}

	// Chỉ xe đang được client lái VÀ camera đang gắn mới nhận input (phanh/ga/lái).
	private bool IsActivelyDriven()
	{
		if (devMode) return true;
		return trafficer.existState == ExistState.ClientControlled
			&& CameraController.Instance != null
			&& CameraController.Instance.CurrentTrafficer == trafficer;
	}

    private void OnBrakeReleased(object sender, EventArgs e)
    {
		if (IsActivelyDriven() && wheels != null) wheels.Brake(false);
    }

    private void OnBrakePressed(object sender, EventArgs e)
	{
		if (IsActivelyDriven() && wheels != null) wheels.Brake(true);
	}


    // Update is called once per frame
    void FixedUpdate()
    {
		if (pauseSO != null && pauseSO.isPaused)
		{
			if (!rb.isKinematic)
			{
				rb.linearVelocity = Vector3.zero;
				rb.angularVelocity = Vector3.zero;
			}
			return; // tạm dừng → không update gì cả, giữ nguyên pose hiện tại.
		} 
		if (wheels == null) return;
		if (devMode)
		{
			DriveFromInput();
			return;
		}
		if (trafficer.existState == ExistState.ClientControlled
			&& CameraController.Instance != null
			&& CameraController.Instance.CurrentTrafficer == trafficer)
		{
			DriveFromInput();
		}
		else if (trafficer.existState == ExistState.Wrecked)
		{
			wheels.UpdatePoses();
		}
	}

	// Đọc input người chơi và ủy quyền cho WheelController.
	private void DriveFromInput()
	{
		Vector3 input = GameInput.Instance.GetMovementInput();
		wheels.Drive(input.z);
		wheels.Steer(input.x);
		wheels.UpdatePoses();
	}
	private void OnCollisionEnter(Collision collision)
	{
		// Chỉ xe dynamic (client/wreck) mới xử lý — xe kinematic không gây wreck
		if (!trafficer.IsClientOwned) return;

		// Latch crash cho xe người chơi đang lái
		if (trafficer.existState == ExistState.ClientControlled)
			hasCrashed = true;

		// Tìm xe ServerControlled bị tông
		Trafficer otherTrafficer = collision.gameObject.GetComponent<Trafficer>();
		if (otherTrafficer == null || otherTrafficer.existState != ExistState.ServerControlled) return;

		UnityVehicle otherUV = collision.gameObject.GetComponent<UnityVehicle>();
		if (otherUV == null) return;

		// Truyền xung lực để xác xe văng theo hướng va chạm
		otherUV.BecomeWreck(collision.relativeVelocity);
	}

	public void ResetFromPool()
	{
		wreckStartStep = 0;
		hasCrashed = false;
	}

	public void SetState(ExistState state)
	{
		trafficer.existState = state;
	}
	public UnityVehicleData GetUnityVehicleData()
	{
		float[] position = { transform.position.x, transform.position.z };
		float[] forward = { transform.forward.x, transform.forward.z };
		// Khi đang chạy vật lý → báo tốc độ thực từ Rigidbody; ngược lại dùng tốc độ server.
		float reportedSpeed = (rb != null && !rb.isKinematic) ? rb.linearVelocity.magnitude : trafficer.GetSpeed();
		return new UnityVehicleData(
			trafficer.GetId(),
			position,
			forward,
			reportedSpeed,
			trafficer.existState
		);
	}
}
