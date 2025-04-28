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
	private bool previousMouseEnabled = false;
	[SerializeField] private Button closeSimulationButton;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
	{
		QualitySettings.vSyncCount = 1;
		GameInput.Instance.OnToggleOptions += (sender, args) =>
		{
			gameObject.SetActive(!gameObject.activeSelf);
			if (gameObject.activeSelf)
			{
				previousMouseEnabled = GameInput.Instance.MouseEnabled;
				GameInput.Instance.SetMouse(true);
			}
			else
			{
				GameInput.Instance.SetMouse(previousMouseEnabled);
			};
			
		};
		closeSimulationButton.onClick.AddListener(() =>
		{
			CloseSimulation();
		});
		StartCoroutine(ManipulateAction.Delay(() =>
		{
			gameObject.SetActive(false);
		}, 0));
	}

	private void CloseSimulation()
	{
		string message = "Simulation end<END>";
		string ip = "127.0.0.1";
		int port = 5054;
		int packetSize = 1024; // bytes per packet
		int maxRetries = 3;
		int timeout = 3000; // milliseconds

		Task.Run(async () =>
		{
			using (TcpClient client = new TcpClient())
			{
				bool connected = false;

				// Retry logic
				for (int attempt = 1; attempt <= maxRetries; attempt++)
				{
					try
					{
						var connectTask = client.ConnectAsync(ip, port);
						if (await Task.WhenAny(connectTask, Task.Delay(timeout)) == connectTask)
						{
							connected = true;
							break;
						}
					}
					catch
					{
						Debug.LogWarning($"Connection attempt {attempt} failed. Retrying...");
						await Task.Delay(timeout);
					}
				}

				if (!connected)
				{
					Debug.LogError("Could not connect to server after retries.");
					return;
				}

				try
				{
					NetworkStream stream = client.GetStream();
					byte[] data = Encoding.UTF8.GetBytes(message);
					int totalLength = data.Length;

					for (int i = 0; i < totalLength; i += packetSize)
					{
						int length = Mathf.Min(packetSize, totalLength - i);
						await stream.WriteAsync(data, i, length);
					}

					stream.Close();
					client.Close();

					Debug.Log("Message sent successfully.");
				}
				catch (SocketException se)
				{
					Debug.LogError($"Socket exception: {se.Message}");
				}
				catch (System.Exception ex)
				{
					Debug.LogError($"Exception during sending: {ex.Message}");
				}
				finally
				{
#if UNITY_EDITOR
					UnityEditor.EditorApplication.isPlaying = false;
#endif
					// Ensure the app exits even if something went wrong
					Application.Quit();

				}
			}
		});
	}
} 
