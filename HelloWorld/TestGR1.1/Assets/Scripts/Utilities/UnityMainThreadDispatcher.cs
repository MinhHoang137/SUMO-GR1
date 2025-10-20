using UnityEngine;
using System.Collections.Generic;
using System;

public class UnityMainThreadDispatcher : MonoBehaviour
{
	private static UnityMainThreadDispatcher instance;
	private readonly Queue<Action> _executionQueue = new Queue<Action>();
	private void Awake()
	{
		if (instance == null)
		{
			instance = this;
			DontDestroyOnLoad(gameObject);
		}
		else
		{
			Destroy(gameObject);
		}
	}
	private void Update()
	{
		while (_executionQueue.Count > 0)
		{
			_executionQueue.Dequeue().Invoke();
		}
	}

	public void Enqueue(Action action)
	{
		_executionQueue.Enqueue(action);
	}
	public static UnityMainThreadDispatcher Instance()
	{
		return instance;
	}
}
