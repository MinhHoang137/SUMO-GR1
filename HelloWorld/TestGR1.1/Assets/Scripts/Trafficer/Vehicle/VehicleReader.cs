using UnityEngine;
using System.Collections.Generic;
using System;
using System.Net.Sockets;
using System.Threading;
using Newtonsoft.Json;
using System.Text;

public class VehicleReader : MonoBehaviour
{
	public class OnReadCompleteEventArgs : EventArgs
	{
		public List<VehicleData> data;
		public OnReadCompleteEventArgs(List<VehicleData> dataArgs)
		{
			this.data = dataArgs;
		}
	}

	public event EventHandler<OnReadCompleteEventArgs> OnReadComplete;

	private TcpListener listener;
	private bool isListening = true;
	private Thread listenerThread;
	private List<VehicleData> data;
	[SerializeField] private string lastJson;

	private const int BUFFER_SIZE = 4096;
	private const string END_MARKER = "<END>";

	void Start()
	{
		StartListening();
	}

	private void StartListening()
	{
		int port = 5051;
		string host = "127.0.0.1";
		listener = new TcpListener(System.Net.IPAddress.Parse(host), port);
		listener.Start();
		Debug.Log($"VehicleReader listening on port {port}...");
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
				using (TcpClient client = listener.AcceptTcpClient())
				using (NetworkStream stream = client.GetStream())
				{
					byte[] buffer = new byte[BUFFER_SIZE];
					StringBuilder fullMessage = new StringBuilder();
					int bytesRead;

					// Đọc liên tục cho đến khi gặp "<END>"
					while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) > 0)
					{
						string chunk = Encoding.UTF8.GetString(buffer, 0, bytesRead);
						fullMessage.Append(chunk);

						// Nếu phát hiện "<END>" thì dừng đọc
						if (fullMessage.ToString().Contains(END_MARKER))
						{
							break;
						}
					}

					// Xử lý dữ liệu sau khi nhận đủ
					string json = fullMessage.ToString().Replace(END_MARKER, "").Trim();

					if (!string.IsNullOrEmpty(json) && json != lastJson)
					{
						lastJson = json;
						HandleData(json);
					}
				}
			}
			catch (SocketException socketEx)
			{
				Debug.LogError($"Socket error: {socketEx.Message}");
			}
			catch (Exception e)
			{
				Debug.LogError($"Error reading vehicle data: {e.Message}");
			}
		}
	}

	private void HandleData(string jsonContent)
	{
		try
		{
			data = JsonConvert.DeserializeObject<List<VehicleData>>(jsonContent);

			if (data != null)
			{
				// Chuyển về main thread để đảm bảo an toàn khi cập nhật UI hoặc xử lý sự kiện
				UnityMainThreadDispatcher.Instance().Enqueue(() =>
				{
					OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs(data));
				});
			}
		}
		catch (Exception e)
		{
			Debug.LogError($"Error parsing vehicle data: {e.Message}");
		}
	}

	void OnDestroy()
	{
		isListening = false;
		listener?.Stop();

		if (listenerThread != null && listenerThread.IsAlive)
		{
			listenerThread.Abort(); // Kết thúc luồng nếu nó còn chạy
		}
	}
}
