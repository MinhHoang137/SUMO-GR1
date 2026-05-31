using Newtonsoft.Json;
using System.Collections.Generic;
using System.Net.Sockets;
using System;
using UnityEngine;
using System.Threading;

public class VehicleSender : MonoBehaviour
{
	private const int BUFFER_SIZE = 131072; // 128 KB

	private Thread sendThread;
	// Chỉ giữ batch MỚI NHẤT (snapshot mọi xe client-owned). Server overwrite latest mỗi message
	// nên gửi từng xe lẻ sẽ mất xe — phải gửi cả batch trong 1 message. Batch cũ chưa gửi thì bỏ.
	private List<UnityVehicleData> pendingBatch;
	private readonly object batchLock = new object();
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

	/// <summary>Gửi nguyên 1 batch (snapshot mọi xe client-owned). Gửi cả batch rỗng để server reconcile xoá xe đã mất.</summary>
	public void SendBatch(List<UnityVehicleData> batch)
	{
		if (batch == null) return;
		lock (batchLock)
		{
			pendingBatch = batch; // thay-ghi: chỉ batch mới nhất là sự thật
		}
		queueSignal.Set();
	}

	private void SendLoop()
	{
		while (isRunning)
		{
			List<UnityVehicleData> batch;
			lock (batchLock)
			{
				batch = pendingBatch;
				pendingBatch = null;
			}

			if (batch == null)
			{
				queueSignal.WaitOne(); // Đợi đến khi có batch mới
				continue;
			}

			// Lỗi kết nối / gửi → bỏ batch này (batch mới sẽ tới ngay sau 0.1s), không requeue.
			if (!EnsureConnected())
			{
				queueSignal.WaitOne(reconnectDelayMillis);
				continue;
			}

			try
			{
				sendJson = JsonConvert.SerializeObject(batch);
				if (!Network.SendMessage(persistentClient, sendJson, BUFFER_SIZE, "<END>"))
				{
					throw new Exception("Failed to send message");
				}
			}
			catch (Exception ex)
			{
				Debug.LogError($"[Unity] Lỗi khi gửi dữ liệu: {ex.Message}");
				CleanupConnection();
				queueSignal.WaitOne(reconnectDelayMillis);
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
