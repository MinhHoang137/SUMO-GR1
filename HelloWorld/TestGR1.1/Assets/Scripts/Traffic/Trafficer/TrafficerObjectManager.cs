using UnityEngine;
using System.Collections.Generic;

/// <summary>
/// Quản lý các đối tượng Trafficer (xe cộ) chung cho các loại Trafficer khác nhau, sử dụng hệ thống pooling để tái sử dụng đối tượng.
/// (Hiện tại khá vô dụng do chỉ có PedestrianManager kế thừa)
/// </summary>
/// <typeparam name="T"></typeparam>
/// <typeparam name="TData"></typeparam>
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
		obj.transform.position = Converter.ToVector3(data.position);
		Vector3 forward = Converter.ToVector3(data.forward);
		Vector3 planarForward = new Vector3(forward.x, 0f, forward.z);
		if (planarForward.sqrMagnitude < 1e-6f) planarForward = Vector3.forward;
		obj.transform.forward = planarForward.normalized;
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

