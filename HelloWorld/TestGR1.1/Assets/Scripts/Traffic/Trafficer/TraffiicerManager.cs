using System.Collections.Generic;
using UnityEngine;
using System;

public class TrafficerManager : MonoBehaviour
{
	public class TrafficerEventArgs : EventArgs
	{
		private Trafficer trafficer;
		public TrafficerEventArgs(Trafficer trafficer)
		{
			this.trafficer = trafficer;
		}
		public Trafficer Trafficer
		{
			get { return trafficer; }
		}
	}
	public class LatencyEventArgs : EventArgs
	{
		public LatencyEventArgs(long latencyMs)
		{
			LatencyMs = latencyMs;
		}
		// Độ trễ của step vừa nhận (mili-giây, số nguyên).
		public long LatencyMs { get; }
	}

	public event EventHandler<TrafficerEventArgs> OnAddTrafficer;
	public event EventHandler<TrafficerEventArgs> OnRemoveTrafficer;

	// Bắn mỗi khi hoàn thành 1 step, mang theo độ trễ end-to-end (mili-giây) so với server.
	// UI/logger subscribe để hiển thị độ trễ realtime.
	public event EventHandler<LatencyEventArgs> OnLatencyChanged;

	public static TrafficerManager Instance { get; private set; }

	// Bước SUMO mới nhất (server gửi qua field "st"). Dùng cho vòng đời xác xe (Wrecked).
	public int CurrentStep { get; set; }

	// Độ trễ end-to-end (mili-giây) của step gần nhất = thời điểm nhận tại Unity - timestamp server gửi ("ts").
	// Yêu cầu đồng hồ 2 máy đồng bộ; localhost (cùng máy) thì chính xác.
	public long LatencyMs { get; private set; }
	// Số bước SUMO xác xe tồn tại trước khi bị despawn.
	[SerializeField, Min(0)] private int wreckLifetimeSteps = 150;
	[SerializeField] private TrafficerKeyPrefabSO trafficerKeyPrefabSO;
	
	private Dictionary<string, Trafficer> trafficerDict = new Dictionary<string, Trafficer>();
	private Dictionary<string, Queue<Trafficer>> trafficerPool = new Dictionary<string, Queue<Trafficer>>();

	private void Awake()
	{
		if (Instance == null)
		{
			Instance = this;
		}
	}

	public void ProcessData(List<TrafficerData> datas, bool isReplay = false)
	{
		if (datas == null) return;
		if (isReplay)
		{
			// Nếu là replay, xóa hết trafficer hiện tại trước khi tạo mới
			DisposeAllTrafficers();
		}
		List<Trafficer> trafficerList = new List<Trafficer>(trafficerDict.Values);
		// Vòng 1: đánh dấu "chưa thấy frame này" cho các xe do server điều khiển.
		// Bỏ qua xe client sở hữu (đang lái / xác xe) — vòng đời của chúng không do server quyết.
		foreach (var trafficer in trafficerList)
		{
			if (trafficer.IsClientOwned) continue;
			trafficer.seenThisFrame = false;
		}

		// Vòng 2: áp dữ liệu từ server.
		foreach (var data in datas)
		{
			Trafficer currentTrafficer = null;
			if (trafficerDict.TryGetValue(data.id, out Trafficer trafficer))
			{
				// SUMO vẫn stream xe đã chuyển sang client/wreck → lờ đi, không ghi đè vị trí.
				if (trafficer.IsClientOwned) continue;
				trafficer.Set(data);
				trafficer.seenThisFrame = true;
				trafficer.existState = ExistState.ServerControlled;
				currentTrafficer = trafficer;
			}
			else
			{
				currentTrafficer = SpawnTrafficer(data);
			}
			if (isReplay && currentTrafficer != null)
			{
				currentTrafficer.transform.position = Converter.ToVector3(data.position);
			}
		}

		// Vòng 2.5: despawn xác xe quá hạn (đếm tập trung — độc lập với active/inactive GameObject).
		foreach (var trafficer in trafficerList)
		{
			if (trafficer.existState != ExistState.Wrecked) continue;
			UnityVehicle uv = trafficer.GetComponent<UnityVehicle>();
			if (uv != null && CurrentStep - uv.wreckStartStep >= wreckLifetimeSteps)
				trafficer.existState = ExistState.Destroyed;
		}

		// Vòng 3: recycle xe hết vòng đời (Destroyed) hoặc xe server không còn được stream.
		foreach (var trafficer in trafficerList)
		{
			bool serverDropped = !trafficer.IsClientOwned && !trafficer.seenThisFrame;
			if (trafficer.existState == ExistState.Destroyed || serverDropped)
			{
				RecycleTrafficer(trafficer);
				// Chỉ xe máy khách (CLIENT_CAR) bị hủy hẳn; xe server quay về pool.
				if (trafficer.isStandaloneClient) Destroy(trafficer.gameObject);
			}
		}
	}

	// Gọi sau khi xử lý xong dữ liệu 1 step. Tính độ trễ end-to-end so với timestamp server
	// rồi bắn OnLatencyChanged. serverTimeMs <= 0 (vd replay không có "ts") → bỏ qua.
	public void ReportStepLatency(long serverTimeMs)
	{
		if (serverTimeMs <= 0) return;

		long nowMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
		long latency = nowMs - serverTimeMs;
		// Chống nhiễu khi đồng hồ lệch âm.
		if (latency < 0) latency = 0;

		LatencyMs = latency;
		OnLatencyChanged?.Invoke(this, new LatencyEventArgs(LatencyMs));
	}

	private Trafficer SpawnTrafficer(TrafficerData data)
	{
		Trafficer prefab = trafficerKeyPrefabSO.GetRandomTrafficer(data.Type);
		if (prefab == null) return null;

		Trafficer trafficer = GetTrafficerFromPool(data.Type, prefab);
		trafficer.transform.position = Converter.ToVector3(data.position);

		if (data.forward != null && data.forward.Length >= 2)
		{
			// SUMO angle compass: forward[0]=cos=Y_north (SUMO.y), forward[1]=sin=X_east (SUMO.x).
			// Map SUMO(x,y) → Unity(x,z) ⇒ Unity.x = forward[1], Unity.z = forward[0]. Khớp Trafficer.Set.
			trafficer.transform.forward = new Vector3(data.forward[1], 0, data.forward[0]);
		}
		
		trafficer.Set(data);
		trafficer.existState = ExistState.ServerControlled;
		trafficer.seenThisFrame = true;
		// Gán type gốc vào tên (hoặc dùng để track lúc recycle)
		trafficer.name = data.Type + "_" + data.id;
		trafficer.transform.SetParent(transform);
		trafficer.gameObject.SetActive(true);
		
		if (!trafficerDict.ContainsKey(trafficer.GetId()))
		{
			trafficerDict.Add(trafficer.GetId(), trafficer);
			OnAddTrafficer?.Invoke(this, new TrafficerEventArgs(trafficer));
		}
		return trafficer;
	}

	private void RecycleTrafficer(Trafficer trafficer)
	{
		trafficerDict.Remove(trafficer.GetId());
		OnRemoveTrafficer?.Invoke(this, new TrafficerEventArgs(trafficer));
		trafficer.gameObject.SetActive(false);

		if (!trafficer.isStandaloneClient)
		{
			// Pool by type
			string poolKey = "v";
			if (trafficer.name.ToLower().Contains("p"))
			{
				poolKey = "p";
			}

			if (!trafficerPool.ContainsKey(poolKey))
			{
				trafficerPool[poolKey] = new Queue<Trafficer>();
			}
			trafficerPool[poolKey].Enqueue(trafficer);
		}
	}

	private Trafficer GetTrafficerFromPool(string type, Trafficer prefab)
	{
		if (!trafficerPool.ContainsKey(type))
		{
			trafficerPool[type] = new Queue<Trafficer>();
		}

		if (trafficerPool[type].Count > 0)
		{
			return trafficerPool[type].Dequeue();
		}
		else
		{
			return Instantiate(prefab);
		}
	}

	public void AddTrafficer(Trafficer trafficer)
	{
		if (!trafficerDict.ContainsKey(trafficer.GetId()))
		{
			trafficerDict.Add(trafficer.GetId(), trafficer);
			OnAddTrafficer?.Invoke(this, new TrafficerEventArgs(trafficer));
		}
		else
		{
			Debug.LogError($"Trafficer with ID {trafficer.GetId()} already exists.");
		}
	}
	// chỉ dùng ở chế độ replay để đảm bảo không ảnh hưởng pool
	private void DisposeAllTrafficers()
	{
		List<Trafficer> trafficerList = new List<Trafficer>(trafficerDict.Values);
		foreach (var trafficer in trafficerList)
		{
			if (trafficer.isStandaloneClient) continue;  // giữ xe máy khách
			RecycleTrafficer(trafficer);
		}
	}

	public void RemoveTrafficer(Trafficer trafficer)
	{
		if (trafficerDict.ContainsKey(trafficer.GetId()))
		{
			trafficerDict.Remove(trafficer.GetId());
			OnRemoveTrafficer?.Invoke(this, new TrafficerEventArgs(trafficer));
		}
		else
		{
			Debug.LogError($"Trafficer with ID {trafficer.GetId()} does not exist.");
		}
	}

	public List<Trafficer> GetTrafficers()
	{
		return new List<Trafficer>(trafficerDict.Values);
	}

	public Trafficer GetTrafficer(string id)
	{
		if (trafficerDict.TryGetValue(id, out Trafficer trafficer))
		{
			return trafficer;
		}
		return null;
	}

	private void OnDestroy()
	{
		Instance = null;
	}
}