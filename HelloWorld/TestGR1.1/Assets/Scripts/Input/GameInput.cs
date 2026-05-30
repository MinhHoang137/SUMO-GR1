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
	public event EventHandler<SwitchEventArgs> OnSwitchForward;
	public event EventHandler<SwitchEventArgs> OnSwitchBackward;

	public event EventHandler OnToggleController;
	public event EventHandler OnToggleOptions;
	public event EventHandler OnMouseToggle;

	public event EventHandler OnBrakePressed;
	public event EventHandler OnBrakeReleased;

	private InputSystem_Actions inputActions;
	private bool mouseEnabled = false;

	private void Awake()
	{
		if (Instance != null)
		{
			Destroy(this);
			return;
		}
		Instance = this;
		inputActions = new InputSystem_Actions();
		inputActions.Enable();
		inputActions.CameraMap.SetFreeToggle.performed += SetFreeToggle_performed;
		inputActions.CameraMap.MouseToggle.performed += MouseToggle_performed;
		//inputActions.CameraMap.MouseToggle.canceled += MouseToggle_performed;
		inputActions.CameraMap.SwitchBackward.performed += SwitchBackward_performed;
		inputActions.CameraMap.SwitchForward.performed += SwitchForward_performed;
		inputActions.CameraMap.Brake.performed += Brake_performed;
		inputActions.CameraMap.Brake.canceled += Brake_canceled;
		inputActions.UI.ToggleController.performed += ToggleController_performed;
		inputActions.UI.ToggleOptions.performed += ToggleOptions_performed;

		// SetMouse(false);
		DontDestroyOnLoad(this.gameObject);
	}

    private void Brake_canceled(InputAction.CallbackContext context)
    {
        OnBrakeReleased?.Invoke(this, EventArgs.Empty);
    }

    private void Brake_performed(InputAction.CallbackContext context)
    {
        OnBrakePressed?.Invoke(this, EventArgs.Empty);
    }

    private void ToggleOptions_performed(InputAction.CallbackContext obj)
	{
		OnToggleOptions?.Invoke(this, EventArgs.Empty);
	}

	private void ToggleController_performed(InputAction.CallbackContext obj)
	{
		OnToggleController?.Invoke(this, EventArgs.Empty);
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
		// SetMouse(!mouseEnabled);
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
	public void SetMouse(bool enabled)
	{
		mouseEnabled = enabled;
		Cursor.lockState = enabled ? CursorLockMode.None : CursorLockMode.Locked;
		Cursor.visible = enabled;
	}
	// public bool MouseEnabled { get { return mouseEnabled; } }
	public Vector2 GetMouseDelta()
	{
		return inputActions.CameraMap.Look.ReadValue<Vector2>();
	}
	public string GetBindingText(Binding binding)
	{
		return binding switch
		{
			Binding.MoveUp => inputActions.CameraMap.Move.bindings[1].ToDisplayString(),
			Binding.MoveDown => inputActions.CameraMap.Move.bindings[2].ToDisplayString(),
			Binding.MoveLeft => inputActions.CameraMap.Move.bindings[3].ToDisplayString(),
			Binding.MoveRight => inputActions.CameraMap.Move.bindings[4].ToDisplayString(),
			Binding.FreeToggle => inputActions.CameraMap.SetFreeToggle.bindings[0].ToDisplayString(),
			Binding.MouseToggle => inputActions.CameraMap.MouseToggle.bindings[0].ToDisplayString(),
			Binding.ToggleController => inputActions.UI.ToggleController.bindings[0].ToDisplayString(),
			Binding.ToggleOptions => inputActions.UI.ToggleOptions.bindings[0].ToDisplayString(),
			_ => "",
		};
	}
}
