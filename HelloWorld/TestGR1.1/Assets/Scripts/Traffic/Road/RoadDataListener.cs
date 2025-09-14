using Newtonsoft.Json;
using System.Net.Sockets;
using System.Net;
using System.Text;
using System.Threading;
using System;
using UnityEngine;

public class RoadDataListener : MonoBehaviour
{

	[SerializeField] private RoadDataSO roadDataSO;

	private RoadData roadData;
	private TcpListener listener;
	private bool isListening = true;
	private Thread listenerThread;
	private string lastJson;

	private const int BUFFER_SIZE = 4096;
	private const string END_MARKER = "<END>";

	protected int port = 5050;


	void Start()
	{
		StartListening();
	}

	private void StartListening()
	{
		string host = "127.0.0.1";
		listener = new TcpListener(IPAddress.Parse(host), port);
		listener.Start();
		Debug.Log($"{GetType().Name} listening on port {port}...");

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
						UnityMainThreadDispatcher.Instance().Enqueue(() =>
						{
							HandleData(json);
						});
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
			roadData = JsonConvert.DeserializeObject<RoadData>(jsonContent);
			//RoadDataSO newRoadDataSO = JsonConvert.DeserializeObject<RoadDataSO>(jsonContent);
			if (roadData != null)
			{
				roadDataSO.edgeDatas = roadData.EdgeDatas;
				roadDataSO.junctionDatas = roadData.JunctionDatas;
				roadDataSO.crossingDatas = roadData.CrossingDatas;
				//roadDataSO.edgeDatas = newRoadDataSO.edgeDatas;
				//roadDataSO.junctionDatas = newRoadDataSO.junctionDatas;
				//roadDataSO.crossingDatas = newRoadDataSO.crossingDatas;
				isListening = false; // Stop listening after processing data
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

	public bool IsListening()
	{
		return isListening;
	}
}
