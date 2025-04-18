using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class CameraControllerUI : MonoBehaviour
{
    [SerializeField] private Slider senseSlider;
    [SerializeField] private TMP_InputField senseInputField;
    private float senseValue = 10;

	[SerializeField] private Slider speedSlider;
	[SerializeField] private TMP_InputField speedInputField;
	private float speedValue = 50;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		senseSlider.value = senseValue;
		speedSlider.value = speedValue;
		CameraController.Instance.Sensitivity = senseValue;
		CameraController.Instance.Speed = speedValue;
		senseInputField.text = senseValue.ToString("0.00");
		speedInputField.text = speedValue.ToString("0.00");

		senseSlider.onValueChanged.AddListener((value) =>
		{
			senseValue = value;
			senseInputField.text = value.ToString("0.00");
			CameraController.Instance.Sensitivity = senseValue;
		});
		senseInputField.onEndEdit.AddListener((value) =>
		{
			if (float.TryParse(value, out float result))
			{
				senseValue = result;
				senseSlider.value = result;
				CameraController.Instance.Sensitivity = senseValue;
			}
			else
			{
				senseInputField.text = senseValue.ToString("0.00");
			}
		});
		speedSlider.onValueChanged.AddListener((value) =>
		{
			speedValue = value;
			speedInputField.text = value.ToString("0.00");
			CameraController.Instance.Speed = speedValue;
		});
		speedInputField.onEndEdit.AddListener((value) =>
		{
			if (float.TryParse(value, out float result))
			{
				speedValue = result;
				speedSlider.value = result;
				CameraController.Instance.Speed = speedValue;
			}
			else
			{
				speedInputField.text = speedValue.ToString("0.00");
			}
		});
	}
}
