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
	private Dictionary<string, Trafficer> trafficerDict = new Dictionary<string, Trafficer>();
	private void Awake()
	{
		Instance = this;
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
		List<Trafficer> trafficers = new(trafficerDict.Values);
		return trafficers;
	}
	public Trafficer GetTrafficer(string id)
	{
		if (trafficerDict.TryGetValue(id, out Trafficer trafficer))
		{
			return trafficer;
		}
		return null;
	}
}
