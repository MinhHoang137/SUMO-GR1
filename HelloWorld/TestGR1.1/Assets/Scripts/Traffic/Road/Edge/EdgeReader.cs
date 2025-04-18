using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Collections.Generic;
using System;
using System.Threading;
using Newtonsoft.Json;

public class EdgeReader : MonoBehaviour
{
	[SerializeField] private RoadData roadData;
	private Thread listenerThread;
	private bool isListening = true;
	private const int port = 5052;
	private const string EOF_MARKER = "__EOF__";

	private void Start()
	{
		listenerThread = new Thread(ListenForData);
		listenerThread.IsBackground = true;
		listenerThread.Start();
	}

	private void ListenForData()
	{
		TcpListener listener = null;

		try
		{
			listener = new TcpListener(IPAddress.Parse("127.0.0.1"), port);
			listener.Start();
			Debug.Log($"EdgeReader listening on port {port}...");

			while (isListening)
			{
				TcpClient client = listener.AcceptTcpClient();
				NetworkStream stream = client.GetStream();

				byte[] buffer = new byte[4096];
				StringBuilder fullMessage = new StringBuilder();
				int bytesRead;

				while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) > 0)
				{
					string chunk = Encoding.UTF8.GetString(buffer, 0, bytesRead);
					fullMessage.Append(chunk);

					if (fullMessage.ToString().Contains(EOF_MARKER))
					{
						string json = fullMessage.ToString().Replace(EOF_MARKER, "");
						ProcessEdgeData(json);
						break;
					}
				}

				client.Close();
				isListening = false; // Dừng sau khi nhận xong dữ liệu
			}
		}
		catch (Exception e)
		{
			Debug.LogError($"Error in EdgeReader: {e.Message}");
		}
		finally
		{
			listener?.Stop();
			listenerThread?.Abort();
		}
	}

	private void ProcessEdgeData(string jsonContent)
	{
		try
		{
			List<EdgeData> edges = JsonConvert.DeserializeObject<List<EdgeData>>(jsonContent);
			if (edges != null)
			{
				UnityMainThreadDispatcher.Instance().Enqueue(() =>
				{
					roadData.edgeDatas = edges;
					Debug.Log($"Received and applied {edges.Count} edges.");
				});
			}
		}
		catch (Exception e)
		{
			Debug.LogError($"Failed to parse edge data: {e.Message}");
		}
	}

	private void OnDestroy()
	{
		isListening = false;
		listenerThread?.Abort();
	}
	public bool IsListening()
	{
		return isListening;
	}
}
