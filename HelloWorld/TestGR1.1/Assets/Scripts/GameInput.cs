using System;
using UnityEngine;
using UnityEngine.InputSystem;

public class GameInput : MonoBehaviour
{
	public static GameInput Instance { get; private set; }
	public class SwitchEventArgs : EventArgs
	{
		public int direction;
		public SwitchEventArgs(int direction)
		{
			this.direction = direction;
		}
	}
	public event EventHandler OnFreeToggle;
	public event EventHandler OnMouseToggle;
	public event EventHandler<SwitchEventArgs> OnSwitchForward;
	public event EventHandler<SwitchEventArgs> OnSwitchBackward;
	private InputSystem_Actions inputActions;

	private void Awake()
	{
		Instance = this;
		inputActions = new InputSystem_Actions();
		inputActions.Enable();
		inputActions.CameraMap.SetFreeToggle.performed += SetFreeToggle_performed;
		inputActions.CameraMap.MouseToggle.performed += MouseToggle_performed;
		//inputActions.CameraMap.MouseToggle.canceled += MouseToggle_performed;
		inputActions.CameraMap.SwitchBackward.performed += SwitchBackward_performed;
		inputActions.CameraMap.SwitchForward.performed += SwitchForward_performed;
	}

	private void SwitchForward_performed(InputAction.CallbackContext obj)
	{
		OnSwitchForward?.Invoke(this, new SwitchEventArgs(1));
	}

	private void SwitchBackward_performed(InputAction.CallbackContext obj)
	{
		OnSwitchBackward?.Invoke(this, new SwitchEventArgs(-1));
	}

	private void MouseToggle_performed(InputAction.CallbackContext obj)
	{
		OnMouseToggle?.Invoke(this, EventArgs.Empty);
	}

	private void SetFreeToggle_performed(InputAction.CallbackContext obj)
	{
		OnFreeToggle?.Invoke(this, EventArgs.Empty);
	}
	public Vector3 GetMovementInput()
	{
		Vector2 inputVec = inputActions.CameraMap.Move.ReadValue<Vector2>();
		return new Vector3(inputVec.x, 0, inputVec.y).normalized;
	}
}
