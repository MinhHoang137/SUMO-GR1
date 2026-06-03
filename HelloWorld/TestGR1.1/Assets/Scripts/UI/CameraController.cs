using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

public class CameraController : MonoBehaviour
{
	public class OnSetTrafficerEventArgs: EventArgs
	{
		public string state;
		public Trafficer preTrafficer;
		public Trafficer newTrafficer;
	}
	public event EventHandler<OnSetTrafficerEventArgs> OnSetTrafficer;
	public event EventHandler OnCameraMove;

	public static CameraController Instance { get; private set; }
	private float speed = 7;
	private float sensitivity = 10;
	private bool isFree = true;
	private Trafficer currentTrafficer;
	[SerializeField] private RoadDataSO roadData;
	[Header("Select Trafficer")]
	[SerializeField] private float selectRange = 100f;

	[Header("Optimization")]
	private Vector3 lastPosition;
	[SerializeField] private float moveThreshold = 100f;

	[Header("Free Camera Leveling")]
	[Tooltip("Tốc độ lerp roll (trục Z) về 0 khi camera trả về tự do.")]
	[SerializeField] private float rollLevelSpeed = 8f;
	private bool isLevelingRoll = false;
	private void Awake()
	{
		Instance = this;
	}
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
	{
		GameInput.Instance.OnFreeToggle += (sender, e) => SetFreeToggle();
		GameInput.Instance.OnSwitchForward += (sender, e) => SetTrafficerView(e.direction);
		GameInput.Instance.OnSwitchBackward += (sender, e) => SetTrafficerView(e.direction);

		// Initialize camera position
		float medianX = 0f;
		float medianZ = 0f;
		float y = 30f;
		foreach (var junction in roadData.junctionDatas)
		{
			medianX += junction.position[0];
			medianZ += junction.position[1];
		}
		medianX /= roadData.junctionDatas.Count;
		medianZ /= roadData.junctionDatas.Count;
		transform.position = new Vector3(medianX, y, medianZ);
		lastPosition = transform.position;
	}

	// Update is called once per frame
	void Update()
	{
		Move();
		Rotate();
		LevelRoll();
	}
	private void Move()
	{
		if (Vector3.Distance(transform.position, lastPosition) > moveThreshold)
		{
			lastPosition = transform.position;
			OnCameraMove?.Invoke(this, EventArgs.Empty);
		}
		if (!isFree) return;
		Vector3 input = GameInput.Instance.GetMovementInput();
		Vector3 move = transform.right * input.x + transform.forward * input.z;
		transform.position += speed * Time.deltaTime * move.normalized;
	}
	private void Rotate()
	{
		// if (GameInput.Instance.MouseEnabled) return;
		if (CursorManager.Instance != null && !CursorManager.Instance.IsCursorLocked())
		{
			return;
		}
		Vector2 delta = GameInput.Instance.GetMouseDelta();
		float mouseX = delta.x * sensitivity * Time.deltaTime;
		float mouseY = delta.y * sensitivity * Time.deltaTime;
		if (transform.eulerAngles.x - mouseY > 90 && transform.eulerAngles.x - mouseY < 270)
		{
			mouseY = 0;
		}
		transform.Rotate(Vector3.left * mouseY);
		transform.Rotate(Vector3.up * mouseX, Space.World);
	}
	// Lerp roll (trục Z) về 0 khi camera về tự do — xe có thể bị lật nghiêng nên world-rotation thừa hưởng roll.
	private void LevelRoll()
	{
		if (!isLevelingRoll) return;
		Vector3 e = transform.eulerAngles;
		float z = Mathf.LerpAngle(e.z, 0f, Time.deltaTime * rollLevelSpeed);
		transform.eulerAngles = new Vector3(e.x, e.y, z);
		if (Mathf.Abs(Mathf.DeltaAngle(z, 0f)) < 0.05f)
		{
			transform.eulerAngles = new Vector3(e.x, e.y, 0f);
			isLevelingRoll = false;
		}
	}
	private void SetFreeToggle()
	{
		if (!PointAndSelectTrafficer())
		{
			SetTrafficerView((Trafficer)null);
			//GameInput.Instance.EnableMove(true);
		}
		// SetTrafficerView (cả nhánh chọn xe lẫn nhánh null) đã bắn OnSetTrafficer với newTrafficer đúng.
		// KHÔNG bắn lại sự kiện null ở đây — nó sẽ ghi đè newTrafficer=xe → ẩn nhầm nút chiếm quyền.
	}
	public void SetRandomTrafficerView()
	{
		List<Trafficer> trafficers = TrafficerManager.Instance.GetTrafficers();
		if (trafficers.Count == 0)
		{
			if (!isFree) SetFreeToggle();
			return;
		}
		int index = UnityEngine.Random.Range(0, trafficers.Count);
		//GameInput.Instance.EnableMove(false);
		try
		{
			SetTrafficerView(trafficers[index]);
		}
		catch (Exception e)
		{
			Debug.Log(e.Message);
		}
	}
	private void SetTrafficerView(int direction)
	{
		if (isFree) return;
		//if (mouseEnabled) return;
		List<Trafficer> trafficers = TrafficerManager.Instance.GetTrafficers();
		if (trafficers.Count == 0) return;
		Trafficer trafficer = transform.GetComponentInParent<Trafficer>();
		if (trafficer == null) return;
		int index = trafficers.IndexOf(trafficer);
		index += direction;
		if (index < 0) index = trafficers.Count - 1;
		if (index >= trafficers.Count) index = 0;
		SetTrafficerView(trafficers[index]);
	}
	private void OnDestroy()
	{
		if (Instance == this)
		{
			Instance = null;
		}
	}
	public Trafficer CurrentTrafficer
	{
		get { return currentTrafficer; }
	}
	public void SetTrafficerView(Trafficer newTrafficer)
	{
		if (newTrafficer == null) {
			transform.SetParent(null);
			isFree = true;
			isLevelingRoll = true;
			OnSetTrafficer?.Invoke(this, new OnSetTrafficerEventArgs()
			{
				state = GetState(),
				preTrafficer = currentTrafficer,
				newTrafficer = null
			});
			currentTrafficer = null;
			return;
		}
		isFree = false;
		transform.SetParent(newTrafficer.GetCameraHolder());
		Trafficer preTrafficer = currentTrafficer;
		currentTrafficer = newTrafficer;
		transform.localPosition = Vector3.zero;
		transform.localEulerAngles = Vector3.zero;
		OnSetTrafficer?.Invoke(this, new OnSetTrafficerEventArgs()
		{
			state = GetState(),
			preTrafficer = preTrafficer,
			newTrafficer = newTrafficer
		});
	}
	public void SetTrafficerView(string id)
	{
		if (!string.IsNullOrEmpty(id)) { 
			return; 
		}
		Trafficer trafficer = TrafficerManager.Instance.GetTrafficer(id);
		Debug.Log($"Set Trafficer View: {trafficer.GetId()}");
		if (trafficer == null) { 
			return; 
		}
		SetTrafficerView(trafficer);
	}
	private bool PointAndSelectTrafficer()
	{
		Ray ray;
		if (!CursorManager.Instance.IsCursorLocked())
		{
			ray = Camera.main.ScreenPointToRay(Input.mousePosition);
		}
		else
		{
			ray = new Ray(transform.position, transform.forward);
		}
		if (Physics.Raycast(ray, out RaycastHit hit, selectRange))
		{
			Trafficer trafficer = hit.transform.GetComponentInParent<Trafficer>();
			if (trafficer != null)
			{
				SetTrafficerView(trafficer);
				return true;
			}
		}
		return false;
	}
	public float Sensitivity
	{
		get { return sensitivity; }
		set { sensitivity = value; }
	}
	public float Speed
	{
		get { return speed; }
		set { speed = value; }
	}
	public string GetState()
	{
		string state = "Trạng thái camera: ";
		if (isFree)
		{
			state += "Tự do";
		}
		else
		{
			state += "gắn vào: " + currentTrafficer.GetId();
		}
		return state;
	}

}
