using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Collections.Generic;
using System;
using System.Threading;
using Newtonsoft.Json;

public class TrafficLightReader : MonoBehaviour
{
	public class OnReadCompleteEventArgs : EventArgs
	{
		public List<TrafficLightData> dataArgs;
	}

	public event EventHandler<OnReadCompleteEventArgs> OnReadComplete;

	private TcpListener listener;
	private bool isListening = true;
	private Thread listenerThread;
	private List<TrafficLightData> data;
	[SerializeField] private string lastJson;

	void Start()
	{
		StartListening();
	}

	private void StartListening()
	{
		int port = 5050;
		listener = new TcpListener(IPAddress.Parse("127.0.0.1"), port);
		listener.Start();
		Debug.Log($"TrafficLightReader listening on port {port}...");

		listenerThread = new Thread(ListenForData);
		listenerThread.IsBackground = true;
		listenerThread.Start();
	}

	private void ListenForData()
	{
		while (isListening)
		{
			try
			{
				TcpClient client = listener.AcceptTcpClient();
				NetworkStream stream = client.GetStream();

				byte[] buffer = new byte[4096];
				StringBuilder fullMessage = new StringBuilder();

				int bytesRead;

				// Đọc nhiều gói cho đến khi nhận được "<END>"
				while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) > 0)
				{
					string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
					fullMessage.Append(message);

					if (fullMessage.ToString().Contains("<END>"))
					{
						// Xóa dấu "<END>" và xử lý dữ liệu
						string json = fullMessage.ToString().Replace("<END>", "");
						if (json != lastJson)
						{
							lastJson = json;
							HandleTrafficLightData(lastJson);
						}					
						break;
					}
				}

				client.Close();
			}
			catch (Exception e)
			{
				Debug.LogError($"Error receiving traffic light data: {e.Message}");
			}
		}
	}

	private void HandleTrafficLightData(string jsonContent)
	{
		try
		{
			data = JsonConvert.DeserializeObject<List<TrafficLightData>>(jsonContent);

			if (data != null)
			{
				// Xử lý trên main thread để tránh conflict luồng
				UnityMainThreadDispatcher.Instance().Enqueue(() =>
				{
					OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs { dataArgs = data });
				});
			}
		}
		catch (Exception e)
		{
			Debug.LogError($"Error parsing traffic light data: {e.Message}");
		}
	}

	void OnDestroy()
	{
		isListening = false;
		listener?.Stop();
		listenerThread?.Abort();
	}
}
