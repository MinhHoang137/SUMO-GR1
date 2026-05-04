using Newtonsoft.Json;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Net;
using System.Text;
using System.Threading;
using System;
using UnityEngine;
using Newtonsoft.Json.Linq;

public class TrafficDataListener : MonoBehaviour
{
	private TcpClient tcpClient;
	private bool isListening = true;
	private Thread listenerThread;
	private TrafficDataList data = new TrafficDataList();
	private string lastJson;

	[SerializeField] private NetworkSO networkSO;
	
	private const int BUFFER_SIZE = 131072;
	private const string END_MARKER = "<END>";

	void Start()
	{
		StartListening();
	}

	private void StartListening()
	{
		tcpClient = Network.CreateTcpClient(networkSO.Host, Constant.DEFAULT_PORT);
		Debug.Log($"{GetType().Name} listening on {networkSO.Host}:{Constant.DEFAULT_PORT}...");

		listenerThread = new Thread(ListenForData)
		{
			IsBackground = true
		};
		listenerThread.Start();
	}

	private void ListenForData()
	{
		Network.SendMessage(tcpClient, "SimulationReady", BUFFER_SIZE, END_MARKER);
		while (isListening)
		{
			try
			{
				string jsonContent = Network.ReadMessage(tcpClient, BUFFER_SIZE, END_MARKER);
				if (!string.IsNullOrEmpty(jsonContent) && jsonContent != lastJson)
				{
					lastJson = jsonContent;
					HandleData(jsonContent);
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
			data = JsonConvert.DeserializeObject<TrafficDataList>(jsonContent);
			if (data != null) { 
				UnityMainThreadDispatcher.Instance().Enqueue(() =>
				{
					TrafficLightManager.Instance.ProcessData(data.TrafficLights);
					TrafficerManager.Instance.ProcessData(data.Trafficers);
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
		Network.CloseTcpClient(tcpClient);
		isListening = false;
		if (listenerThread != null && listenerThread.IsAlive)
		{
			listenerThread.Join();
		}
	}
}
