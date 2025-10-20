using System;
using System.Collections.Generic;
using UnityEngine;

public class CameraController : MonoBehaviour
{
	public class OnSetTrafficerEventArgs: EventArgs {
		private string state;
		public OnSetTrafficerEventArgs(string state)
		{
			this.state = state;
		}
		public string State { get { return state; } }
	}
	public event EventHandler<OnSetTrafficerEventArgs> OnSetTrafficer;

	public static CameraController Instance { get; private set; }
	private float speed = 7;
	private float sensitivity = 10;
	private bool isFree = true;
	private Trafficer currentTrafficer;
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
	}

	// Update is called once per frame
	void Update()
	{
		Move();
		Rotate();
	}
	private void Move()
	{
		if (!isFree) return;
		Vector3 input = GameInput.Instance.GetMovementInput();
		Vector3 move = transform.right * input.x + transform.forward * input.z;
		transform.position += speed * Time.deltaTime * move.normalized;
	}
	private void Rotate()
	{
		if (GameInput.Instance.MouseEnabled) return;
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
	private void SetFreeToggle()
	{
		if (!isFree)
		{
			transform.SetParent(null);
			currentTrafficer = null;
			isFree = true;
			//GameInput.Instance.EnableMove(true);
		}
		else
		{
			SetRandomTrafficerView();
		}
		OnSetTrafficer?.Invoke(this, new OnSetTrafficerEventArgs(GetState()));
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
		Instance = null;
	}
	public Trafficer CurrentTrafficer
	{
		get { return currentTrafficer; }
	}
	public void SetTrafficerView(Trafficer trafficer)
	{
		if (trafficer == null) return;
		isFree = false;
		transform.SetParent(trafficer.GetCameraHolder());
		currentTrafficer = trafficer;
		transform.localPosition = Vector3.zero;
		transform.localEulerAngles = Vector3.zero;
		OnSetTrafficer?.Invoke(this, new OnSetTrafficerEventArgs(GetState()));
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
