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
	private NetworkStream persistentStream;

	public string host = "127.0.0.1";
	public int port = 5053;
	public int timeoutMillis = 1000;
	[SerializeField] private string sendJson;
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
					List<VehicleData> dataList = new List<VehicleData> { vehicleData };
					sendJson = JsonConvert.SerializeObject(dataList) + "<END>";
					byte[] bytesToSend = Encoding.UTF8.GetBytes(sendJson);

					persistentStream.Write(bytesToSend, 0, bytesToSend.Length);
					persistentStream.Flush();
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
			if (persistentClient != null && persistentClient.Connected && persistentStream != null)
			{
				return true;
			}

			CleanupConnection();
			persistentClient = new TcpClient();
			var connectTask = persistentClient.ConnectAsync(host, port);
			if (!connectTask.Wait(timeoutMillis))
			{
				Debug.LogWarning($"[Unity] Timeout khi kết nối tới {host}:{port}");
				CleanupConnection();
				return false;
			}
			persistentClient.ReceiveTimeout = timeoutMillis;
			persistentClient.SendTimeout = timeoutMillis;
			persistentStream = persistentClient.GetStream();
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
		try { persistentStream?.Close(); } catch { }
		try { persistentClient?.Close(); } catch { }
		persistentStream = null;
		persistentClient = null;
	}
}

