using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class CameraControllerUI : MonoBehaviour
{
	[SerializeField] private ValueUI senseUI;
	[SerializeField] private ValueUI speedUI;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		senseUI.Create((value) =>
		{
			CameraController.Instance.Sensitivity = value;
		});
		speedUI.Create((value) =>
		{
			CameraController.Instance.Speed = value;
		});
	}
	private void OnDestroy()
	{
		senseUI.Destroy();
		speedUI.Destroy();
	}
}
