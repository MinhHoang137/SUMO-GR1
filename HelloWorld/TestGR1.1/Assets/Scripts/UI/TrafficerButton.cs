using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class TrafficerButton : MonoBehaviour
{
	[SerializeField] private TMP_Text trafficerId;
	[SerializeField] private Button button;
	private Trafficer trafficer;

	// Start is called once before the first execution of Update after the MonoBehaviour is created

	public void SetTrafficerId(string text)
	{
		trafficerId.text = text;
		trafficer = TrafficerManager.Instance.GetTrafficer(text);
		if (trafficer == null)
		{
			Debug.LogError($"Trafficer with ID {text} not found.");
			return;
		}
		button.onClick.AddListener(() =>
		{
			CameraController.Instance.SetTrafficerView(trafficer);
		});
	}
}
