using UnityEngine;
using System.Collections.Generic;
using System;
using System.Net.Sockets;
using System.Net;
using System.Threading;
using Newtonsoft.Json;
using System.Text;

public abstract class TrafficReader<T> : MonoBehaviour
{
	public class OnReadCompleteEventArgs : EventArgs
	{
		public List<T> data { get; private set; }

		public OnReadCompleteEventArgs(List<T> data)
		{
			this.data = data;
		}
	}

	public event EventHandler<OnReadCompleteEventArgs> OnReadComplete;

	private TcpListener listener;
	private bool isListening = true;
	private Thread listenerThread;
	private List<T> data;
	[SerializeField] private string lastJson;

	private const int BUFFER_SIZE = 4096;
	private const string END_MARKER = "<END>";

	protected abstract int Port { get; }

	void Start()
	{
		StartListening();
	}

	private void StartListening()
	{
		string host = "127.0.0.1";
		listener = new TcpListener(IPAddress.Parse(host), Port);
		listener.Start();
		Debug.Log($"{GetType().Name} listening on port {Port}...");

		listenerThread = new Thread(ListenForData)
		{
			IsBackground = true
		};
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

					while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) > 0)
					{
						string chunk = Encoding.UTF8.GetString(buffer, 0, bytesRead);
						fullMessage.Append(chunk);

						if (fullMessage.ToString().Contains(END_MARKER))
						{
							break;
						}
					}

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
				Debug.LogError($"Socket error in {GetType().Name}: {socketEx.Message}");
			}
			catch (Exception e)
			{
				Debug.LogError($"Error reading data in {GetType().Name}: {e.Message}");
			}
		}
	}

	private void HandleData(string jsonContent)
	{
		try
		{
			data = JsonConvert.DeserializeObject<List<T>>(jsonContent);

			if (data != null)
			{
				UnityMainThreadDispatcher.Instance().Enqueue(() =>
				{
					OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs(data));
				});
			}
		}
		catch (Exception e)
		{
			Debug.LogError($"Error parsing data in {GetType().Name}: {e.Message}");
		}
	}

	void OnDestroy()
	{
		isListening = false;
		listener?.Stop();

		if (listenerThread != null && listenerThread.IsAlive)
		{
			listenerThread.Abort();
		}
	}
}
