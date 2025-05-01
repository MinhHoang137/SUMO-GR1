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

	public string host = "127.0.0.1";
	public int port = 5053;
	public int timeoutMillis = 1000;
	[SerializeField] private string sendJson;

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
				try
				{
					using (TcpClient client = new TcpClient())
					{
						var connectTask = client.ConnectAsync(host, port);
						if (!connectTask.Wait(timeoutMillis))
						{
							Debug.LogWarning($"[Unity] Timeout khi kết nối tới {host}:{port}");
							continue;
						}

						using (NetworkStream stream = client.GetStream())
						{
							List<VehicleData> dataList = new List<VehicleData> { vehicleData };
							sendJson = JsonConvert.SerializeObject(dataList) + "<END>";
							byte[] bytesToSend = Encoding.UTF8.GetBytes(sendJson);

							stream.Write(bytesToSend, 0, bytesToSend.Length);
							stream.Flush();
						}
					}
				}
				catch (SocketException ex)
				{
					Debug.LogError($"[Unity] Socket error: {ex.Message}");
				}
				catch (Exception ex)
				{
					Debug.LogError($"[Unity] Lỗi khi gửi dữ liệu: {ex.Message}");
				}
			}
			else
			{
				queueSignal.WaitOne(); // Đợi đến khi có dữ liệu mới
			}
		}
	}
}

