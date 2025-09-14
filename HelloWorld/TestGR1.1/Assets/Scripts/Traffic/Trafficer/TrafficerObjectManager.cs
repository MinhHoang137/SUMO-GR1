using UnityEngine;
using System.Collections.Generic;

public abstract class TrafficerObjectManager<T, TData> : MonoBehaviour
	where T : Trafficer 
	where TData : TrafficerData
{
	[SerializeField] protected T[] prefabs;
	protected Dictionary<string, T> activeDict = new Dictionary<string, T>();
	protected Dictionary<int, Queue<T>> pool = new Dictionary<int, Queue<T>>();
	protected virtual void StartManager(System.Action onInitialized = null)
	{
		for (int i = 0; i < prefabs.Length; i++)
		{
			pool[i] = new Queue<T>();
		}

		onInitialized?.Invoke();
	}

	public void ProcessData(List<TData> dataList)
	{
		List<T> currentList = new List<T>(activeDict.Values);
		foreach (var item in currentList)
		{
			item.isExist = false;
		}

		foreach (var data in dataList)
		{
			if (activeDict.TryGetValue(data.id, out T obj))
			{
				obj.Set(data);
				obj.isExist = true;
			}
			else
			{
				Spawn(data);
			}
		}

		foreach (var item in currentList)
		{
			if (!item.isExist)
			{
				Recycle(item);
			}
		}
	}

	protected void Spawn(TData data)
	{
		int index = Random.Range(0, prefabs.Length);
		T obj = GetFromPool(index);
		obj.transform.position = new Vector3(data.position[0], 0, data.position[1]);
		obj.transform.forward = new Vector3(data.forward[0], 0, data.forward[1]);
		obj.Set(data);
		obj.isExist = true;
		obj.gameObject.SetActive(true);
		obj.transform.SetParent(transform);
		activeDict.Add(data.id, obj);
		TrafficerManager.Instance.AddTrafficer(obj);
	}

	protected void Recycle(T obj)
	{
		activeDict.Remove(obj.GetId());
		obj.gameObject.SetActive(false);
		int index = GetPrefabIndex(obj);
		if (index != -1)
		{
			pool[index].Enqueue(obj);
		}
		TrafficerManager.Instance.RemoveTrafficer(obj);
	}

	private T GetFromPool(int index)
	{
		if (pool[index].Count > 0)
		{
			return pool[index].Dequeue();
		}
		else
		{
			return Instantiate(prefabs[index]);
		}
	}

	private int GetPrefabIndex(T obj)
	{
		for (int i = 0; i < prefabs.Length; i++)
		{
			if (obj.name.Contains(prefabs[i].name))
			{
				return i;
			}
		}
		return -1;
	}
}

