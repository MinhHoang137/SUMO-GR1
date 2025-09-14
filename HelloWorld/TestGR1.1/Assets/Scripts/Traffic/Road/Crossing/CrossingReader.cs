using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Collections.Generic;
using System;
using System.Threading;
using Newtonsoft.Json;

public class CrossingReader : MonoBehaviour
{
	private TcpListener listener;
	private bool isListening = true;
	private Thread listenerThread;
	private List<CrossingData> crossings;
	[SerializeField] private RoadDataSO roadData;

	private string lastJson;
	private const int port = 5051;
	private const string EOF_MARKER = "__EOF__";

	void Start()
	{
		StartListening();
	}

	private void StartListening()
	{
		listener = new TcpListener(IPAddress.Parse("127.0.0.1"), port);
		listener.Start();
		Debug.Log($"CrossingReader listening on port {port}...");

		listenerThread = new Thread(ListenForData);
		listenerThread.IsBackground = true;
		listenerThread.Start();
	}

	private void ListenForData()
	{
		try
		{
			while (isListening)
			{
				using (TcpClient client = listener.AcceptTcpClient())
				using (NetworkStream stream = client.GetStream())
				{
					byte[] buffer = new byte[4096];
					StringBuilder fullMessage = new StringBuilder();
					int bytesRead;

					while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) > 0)
					{
						string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
						fullMessage.Append(message);

						if (fullMessage.ToString().Contains(EOF_MARKER))
						{
							string json = fullMessage.ToString().Replace(EOF_MARKER, "");
							if (json != lastJson)
							{
								lastJson = json;
								HandleCrossingData(lastJson);
							}
							break;
						}
					}
				}

				isListening = false; // Chỉ lắng nghe 1 lần rồi dừng
			}
		}
		catch (Exception e)
		{
			Debug.LogError($"Error receiving crossing data: {e.Message}");
		}
		finally
		{
			listener?.Stop();
			Debug.Log("CrossingReader stopped listening.");
		}
	}

	private void HandleCrossingData(string jsonContent)
	{
		try
		{
			crossings = JsonConvert.DeserializeObject<List<CrossingData>>(jsonContent);

			if (crossings != null)
			{
				UnityMainThreadDispatcher.Instance().Enqueue(() =>
				{
					roadData.crossingDatas = crossings;
					Debug.Log("Crossing data received and applied to roadData: " + crossings.Count);
				});
			}
		}
		catch (Exception e)
		{
			Debug.LogError($"Error parsing crossing data: {e.Message}");
		}
	}

	void OnDestroy()
	{
		isListening = false;
		if (listener != null)
		{
			listener.Stop();
		}
	}
	public bool IsListening()
	{
		return isListening;
	}
}
