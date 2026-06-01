using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Nút chiếm/trả quyền điều khiển xe đang được camera gắn vào.
/// Độc lập với CameraController — chỉ nghe sự kiện OnSetTrafficer qua singleton,
/// nên gắn ở đâu cũng được (object UI chứa nút, hoặc GameObject CameraController).
///
/// Quy tắc hiển thị nút theo xe camera đang gắn:
///   - không gắn xe / không phải xe lái được (không có UnityVehicle) / xe máy khách / xác xe → ẩn
///   - xe đang ServerControlled → hiện "Chiếm quyền" (TakeControl)
///   - xe đang ClientControlled (do chính client chiếm) → hiện "Trả quyền" (ReleaseControl)
/// Ngoài ra: rời camera khỏi xe đang chiếm → tự trả quyền.
/// </summary>
public class VehicleTakeoverUI : MonoBehaviour
{
	[SerializeField] private Button takeoverButton;
	[SerializeField] private TMP_Text buttonLabel;  // tùy chọn: đổi chữ Chiếm/Trả

	private const string TAKE = "Chiếm quyền";
	private const string RELEASE = "Trả quyền";

	private Trafficer currentTrafficer;
	private UnityVehicle currentVehicle;

	private void Start()
	{
		takeoverButton.onClick.AddListener(OnButtonClicked);
		CameraController.Instance.OnSetTrafficer += OnSetTrafficer;
		Refresh(CameraController.Instance.CurrentTrafficer);
	}

	private void OnDestroy()
	{
		if (CameraController.Instance != null)
		{
			CameraController.Instance.OnSetTrafficer -= OnSetTrafficer;
		}
	}

	private void OnSetTrafficer(object sender, CameraController.OnSetTrafficerEventArgs e)
	{
		// Camera rời một xe đang bị client lái → tự trả quyền (xe tự chạy lại).
		if (e.preTrafficer != null
			&& e.preTrafficer != e.newTrafficer
			&& e.preTrafficer.existState == ExistState.ClientControlled
			&& !e.preTrafficer.isStandaloneClient
			&& e.preTrafficer.TryGetComponent<UnityVehicle>(out var prevVehicle))
		{
			prevVehicle.ReleaseControl();
		}
		Refresh(e.newTrafficer);
	}

	private void Refresh(Trafficer trafficer)
	{
		currentTrafficer = null;
		currentVehicle = null;

		bool canControl = trafficer != null
			&& !trafficer.isStandaloneClient
			&& trafficer.existState != ExistState.Wrecked
			&& trafficer.TryGetComponent<UnityVehicle>(out var vehicle);

		if (!canControl)
		{
			takeoverButton.gameObject.SetActive(false);
			Debug.Log("VehicleTakeoverUI: No controllable vehicle, hiding button.");
			return;
		}

		currentTrafficer = trafficer;
		currentVehicle = trafficer.GetComponent<UnityVehicle>();
		takeoverButton.gameObject.SetActive(true);
		if (buttonLabel != null)
		{
			buttonLabel.text = trafficer.existState == ExistState.ClientControlled ? RELEASE : TAKE;
		}
	}

	private void OnButtonClicked()
	{
		if (currentVehicle == null || currentTrafficer == null) return;

		if (currentTrafficer.existState == ExistState.ServerControlled)
		{
			currentVehicle.TakeControl();
		}
		else if (currentTrafficer.existState == ExistState.ClientControlled)
		{
			currentVehicle.ReleaseControl();
		}
		Refresh(currentTrafficer);  // cập nhật nhãn nút sau khi đổi state
	}
}
