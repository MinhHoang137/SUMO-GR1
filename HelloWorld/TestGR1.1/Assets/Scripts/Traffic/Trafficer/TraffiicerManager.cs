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
	public event EventHandler<TrafficerEventArgs> OnAddTrafficer;
	public event EventHandler<TrafficerEventArgs> OnRemoveTrafficer;

	public static TrafficerManager Instance { get; private set; }
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

	public void ProcessData(List<TrafficerData> datas)
	{
		if (datas == null) return;

		List<Trafficer> trafficerList = new List<Trafficer>(trafficerDict.Values);
		foreach (var trafficer in trafficerList)
		{
			if (trafficer.GetComponent<UnityVehicle>() != null) continue;
			trafficer.isExist = false;
		}

		foreach (var data in datas)
		{
			if (trafficerDict.TryGetValue(data.id, out Trafficer trafficer))
			{
				if (trafficer.GetComponent<UnityVehicle>() != null) continue;
				trafficer.Set(data);
				trafficer.isExist = true;
			}
			else
			{
				SpawnTrafficer(data);
			}
		}

		foreach (var trafficer in trafficerList)
		{
			if (!trafficer.isExist)
			{
				RecycleTrafficer(trafficer);
				if (trafficer.GetComponent<UnityVehicle>() != null) Destroy(trafficer.gameObject);
			}
		}
	}

	private void SpawnTrafficer(TrafficerData data)
	{
		Trafficer prefab = trafficerKeyPrefabSO.GetRandomTrafficer(data.Type);
		if (prefab == null) return;

		Trafficer trafficer = GetTrafficerFromPool(data.Type, prefab);
		trafficer.transform.position = new Vector3(data.position[0], 0, data.position[1]);
		
		if (data.forward != null && data.forward.Length >= 2)
		{
			trafficer.transform.forward = new Vector3(data.forward[0], 0, data.forward[1]);
		}
		
		trafficer.Set(data);
		trafficer.isExist = true;
		// Gán type gốc vào tên (hoặc dùng để track lúc recycle)
		trafficer.name = data.Type + "_" + data.id;
		trafficer.transform.SetParent(transform);
		trafficer.gameObject.SetActive(true);
		
		if (!trafficerDict.ContainsKey(trafficer.GetId()))
		{
			trafficerDict.Add(trafficer.GetId(), trafficer);
			OnAddTrafficer?.Invoke(this, new TrafficerEventArgs(trafficer));
		}
	}

	private void RecycleTrafficer(Trafficer trafficer)
	{
		trafficerDict.Remove(trafficer.GetId());
		OnRemoveTrafficer?.Invoke(this, new TrafficerEventArgs(trafficer));
		trafficer.gameObject.SetActive(false);

		if (trafficer.GetComponent<UnityVehicle>() == null)
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