using Newtonsoft.Json;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Text;
using System;
using UnityEngine;
using System.Threading;

public class VehicleSender : MonoBehaviour
{
	private Thread sendThread;
	private ConcurrentQueue<UnityVehicleData> queue = new();
	private AutoResetEvent queueSignal = new AutoResetEvent(false);
	private bool isRunning = true;

	private TcpClient persistentClient;

	public int timeoutMillis = 1000;
	[SerializeField] private string sendJson;
	[SerializeField] private NetworkSO networkSO;
	public int reconnectDelayMillis = 250; // chờ giữa các lần thử kết nối lại

	void Start()
	{
		sendThread = new Thread(SendLoop);
		sendThread.IsBackground = true;
		sendThread.Start();
	}

	void OnDestroy()
	{
		isRunning = false;
		queueSignal.Set(); // Đánh thức thread để nó kết thúc
		if (sendThread != null && sendThread.IsAlive)
		{
			sendThread.Join();
		}
	}

	public void SendUnityData(UnityVehicleData vehicleData)
	{
		if (vehicleData == null)
		{
			return;
		}
		if (queue.Count < 5) // Giới hạn số lượng dữ liệu trong hàng đợi
		{
			queue.Enqueue(vehicleData);
		}
		queueSignal.Set(); // Đánh thức thread nếu đang chờ
	}

	private void SendLoop()
	{
		while (isRunning)
		{
			if (queue.TryDequeue(out var vehicleData))
			{
				// Đảm bảo có kết nối trước khi gửi
				if (!EnsureConnected())
				{
					// Nếu không kết nối được, đẩy lại dữ liệu vào hàng đợi và chờ một chút
					queue.Enqueue(vehicleData);
					queueSignal.WaitOne(reconnectDelayMillis);
					continue;
				}

				try
				{
					List<UnityVehicleData> dataList = new List<UnityVehicleData> { vehicleData };
					sendJson = JsonConvert.SerializeObject(dataList);
					
					if (!Network.SendMessage(persistentClient, sendJson, 1024, "<END>"))
					{
						throw new Exception("Failed to send message");
					}
				}
				catch (Exception ex)
				{
					Debug.LogError($"[Unity] Lỗi khi gửi dữ liệu: {ex.Message}");
					// nếu có lỗi gửi, đóng kết nối để thử reconnect ở lần sau
					CleanupConnection();
					// đẩy lại dữ liệu để thử gửi sau khi reconnect
					queue.Enqueue(vehicleData);
					queueSignal.WaitOne(reconnectDelayMillis);
				}
			}
			else
			{
				queueSignal.WaitOne(); // Đợi đến khi có dữ liệu mới
			}
		}
	}

	private bool EnsureConnected()
	{
		try
		{
			if (persistentClient != null && persistentClient.Connected)
			{
				return true;
			}

			CleanupConnection();
			persistentClient = Network.CreateTcpClient(networkSO.Host, Constant.SEND_DATA_PORT);
			persistentClient.ReceiveTimeout = timeoutMillis;
			persistentClient.SendTimeout = timeoutMillis;
			return true;
		}
		catch (Exception ex)
		{
			Debug.LogError($"[Unity] Lỗi khi kết nối: {ex.Message}");
			CleanupConnection();
			return false;
		}
	}

	private void CleanupConnection()
	{
		Network.CloseTcpClient(persistentClient);
		persistentClient = null;
	}
}

