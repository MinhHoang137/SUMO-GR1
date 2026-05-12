using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class RealtimePreparer : MonoBehaviour
{
    [SerializeField] private Button startButton;
	[SerializeField] private Button getRoadDataButton;
	[SerializeField] private TMP_InputField hostInputField;
	[SerializeField] private TMP_Text connectResultText;
	[SerializeField] private NetworkSO networkSO;
	[SerializeField] private RoadDataListener roadDataListener;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		hostInputField.text = networkSO.Host;
		startButton.onClick.AddListener(() =>
		{
			if (!roadDataListener.IsListening())
			{
				// cảnh kết nối thời gian thực có index 1 trong Build Settings
				SceneManager.LoadScene(1);
			}
				
		});
		getRoadDataButton.onClick.AddListener(() =>
		{
			roadDataListener.StartListening();
			connectResultText.gameObject.SetActive(true);
			connectResultText.text = "Đang kết nối đến máy chủ...";
			connectResultText.color = Color.white;
		});
		hostInputField.onEndEdit.AddListener((value) =>
		{
			networkSO.Host = value;
		});
		roadDataListener.OnRoadDataReceived.AddListener(OnGetDataSuccess);
		roadDataListener.OnConnectedFailed.AddListener(OnGetDataFailed);
	}
	private void OnGetDataSuccess()
	{
		connectResultText.text = "Dữ liệu bản đồ đã được nhận thành công!";
		connectResultText.color = Color.green;
	}
	private void OnGetDataFailed()
	{
		connectResultText.text = "Không thể kết nối đến máy chủ. \nVui lòng kiểm tra lại địa chỉ IP và thử lại.";
		connectResultText.color = Color.red;
	}

}
