using Newtonsoft.Json;
using System.Net.Sockets;
using System.Net;
using System.Text;
using System.Threading;
using System;
using UnityEngine;
using UnityEngine.Events;

public class RoadDataListener : MonoBehaviour
{

	[SerializeField] private RoadDataSO roadDataSO;
	[SerializeField] private NetworkSO networkSO;
	public UnityEvent OnRoadDataReceived;
	public UnityEvent OnConnectedFailed;

	private RoadData roadData;
	private TcpClient tcpClient;
	private bool isListening = true;
	private Thread listenerThread;
	private string lastJson;

	private const int BUFFER_SIZE = 131072;
	private const string END_MARKER = "<END>";



	void Start()
	{
	}

	public void StartListening()
	{
		try
		{
			tcpClient = Network.CreateTcpClient(networkSO.Host, Constant.DEFAULT_PORT);
			Debug.Log($"{GetType().Name} connected to {networkSO.Host}:{Constant.DEFAULT_PORT}...");

			listenerThread = new Thread(ListenForData)
			{
				IsBackground = true
			};
			listenerThread.Start();
		}
		catch (Exception e)
		{
			Debug.LogError($"Failed to connect in {GetType().Name}: {e.Message}");
			OnConnectedFailed?.Invoke();
		}
	}

	private void ListenForData()
	{
		Network.SendMessage(tcpClient, "RoadDataRequest", BUFFER_SIZE, END_MARKER);
		while (isListening)
		{
			try
			{
				if (tcpClient == null)
				{
					Thread.Sleep(100);
					continue;
				}

				if (!tcpClient.Connected)
				{
					Thread.Sleep(100);
					continue;
				}

				string json = Network.ReadMessage(tcpClient, BUFFER_SIZE, END_MARKER);
				if (!string.IsNullOrEmpty(json) && json != lastJson)
				{
					lastJson = json;
					UnityMainThreadDispatcher.Instance().Enqueue(() => HandleData(json));
				}
			}
			catch (SocketException socketEx)
			{
				Debug.LogError($"Socket error in {GetType().Name}: {socketEx.Message}");
				break;
			}
			catch (Exception e)
			{
				Debug.LogError($"Error reading data in {GetType().Name}: {e.Message}");
				break;
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
				// null ở chế độ không phải OSM → clear danh sách cũ (tránh giữ nhà của lần chạy trước trên SO asset).
				roadDataSO.buildingDatas = roadData.BuildingDatas;
				//roadDataSO.edgeDatas = newRoadDataSO.edgeDatas;
				//roadDataSO.junctionDatas = newRoadDataSO.junctionDatas;
				//roadDataSO.crossingDatas = newRoadDataSO.crossingDatas;
				isListening = false; // Stop listening after processing data
				try { Network.CloseTcpClient(tcpClient); } catch { }
				listenerThread.Abort();
				OnRoadDataReceived?.Invoke();
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
		try { 
			Network.CloseTcpClient(tcpClient);
			Debug.Log($"{GetType().Name} TCP client closed."); 
		} catch { }

		if (listenerThread != null && listenerThread.IsAlive)
		{
			try { listenerThread.Abort(); } catch { }
		}
	}

	public bool IsListening()
	{
		return isListening;
	}
}
