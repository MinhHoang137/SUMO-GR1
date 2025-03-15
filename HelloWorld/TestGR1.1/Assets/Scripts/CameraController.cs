using System.Collections.Generic;
using UnityEngine;

public class CameraController : MonoBehaviour
{
    [SerializeField] private float speed = 7;
    [SerializeField] private float sensitivity = 10;
	private bool mouseEnabled = false;
	private bool isFree = true;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        transform.eulerAngles = Vector3.zero;
		SetMouse(mouseEnabled);
		GameInput.Instance.OnMouseToggle += (sender, e) => SetMouse(!mouseEnabled);
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
		transform.position += move.normalized * speed * Time.deltaTime;
	}
	private void Rotate()
	{
		if (mouseEnabled) return;
		float mouseX = Input.GetAxis("Mouse X") * sensitivity * Time.deltaTime;
		float mouseY = Input.GetAxis("Mouse Y") * sensitivity * Time.deltaTime;
		if (transform.eulerAngles.x - mouseY > 90 && transform.eulerAngles.x - mouseY < 270)
		{
			mouseY = 0;
		}
		transform.Rotate(Vector3.left * mouseY);
		transform.Rotate(Vector3.up * mouseX, Space.World);
	}
	private void SetMouse(bool enabled)
	{
		mouseEnabled = enabled;
		Cursor.lockState = enabled ? CursorLockMode.None : CursorLockMode.Locked;
		Cursor.visible = enabled;
	}
	private void SetFreeToggle()
	{
		if (!isFree) { 
			transform.SetParent(null);
		}
		else
		{
			SetRandomTrafficerView();
		}
		isFree = !isFree;
	}
	public void SetRandomTrafficerView()
	{
		List<Trafficer> trafficers = TrafficerManager.Instance.GetTrafficers();
		if (trafficers.Count == 0) return;
		int index = Random.Range(0, trafficers.Count);
		transform.SetParent(trafficers[index].GetCameraHolder());
		transform.localPosition = Vector3.zero;
		transform.localEulerAngles = Vector3.zero;
	}
	private void SetTrafficerView(int direction)
	{
		if (isFree) return;
		if (mouseEnabled) return;
		List<Trafficer> trafficers = TrafficerManager.Instance.GetTrafficers();
		if (trafficers.Count == 0) return;
		Trafficer trafficer = transform.GetComponentInParent<Trafficer>();
		if (trafficer == null) return;
		int index = trafficers.IndexOf(trafficer);
		index += direction;
		if (index < 0) index = trafficers.Count - 1;
		if (index >= trafficers.Count) index = 0;
		transform.SetParent(trafficers[index].GetCameraHolder());
		transform.localPosition = Vector3.zero;
		transform.localEulerAngles = Vector3.zero;
	}
}
