using TMPro;
using Unity.Collections;
using UnityEngine;
using UnityEngine.UI;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

public class OptionUI : MonoBehaviour
{
	// private bool previousMouseEnabled = false;
	[SerializeField] private NetworkSO networkSO;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
	{
		// QualitySettings.vSyncCount = 1;
		GameInput.Instance.OnToggleOptions += (sender, args) =>
		{
			gameObject.SetActive(!gameObject.activeSelf);
			if (gameObject.activeSelf)
			{
				// previousMouseEnabled = GameInput.Instance.MouseEnabled;
				// GameInput.Instance.SetMouse(true);
			}
			else
			{
				// GameInput.Instance.SetMouse(previousMouseEnabled);
			};
			
		};
		StartCoroutine(ManipulateAction.Delay(() =>
		{
			gameObject.SetActive(false);
		}, 0));
	}

	private void CloseSimulation()
	{
		string message = "Simulation end";
		string ip = networkSO.Host;
		int port = Constant.CMD_PORT;
		int packetSize = 1024; // bytes per packet

		Task.Run(() =>
		{
			TcpClient client = null;
			try
			{
				client = Network.CreateTcpClient(ip, port);
				Network.SendMessage(client, message, packetSize, "<END>");
				Debug.Log("Message sent successfully.");
			}
			catch (System.Exception ex)
			{
				Debug.LogError($"Exception during sending: {ex.Message}");
			}
			finally
			{
				Network.CloseTcpClient(client);
#if UNITY_EDITOR
				UnityEditor.EditorApplication.isPlaying = false;
#endif
				// Ensure the app exits even if something went wrong
				Application.Quit();

			}
		});
	}

    private void OnApplicationQuit()
    {
        CloseSimulation();
    }
} 
