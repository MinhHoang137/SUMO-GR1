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

    private void Update()
    {
        foreach (var trafficer in trafficerDict.Values)
		{

			float scaleRange = 10f;
			float range = CameraController.Instance != null ? CameraController.Instance.GetFarDistance() * scaleRange : 1000f;
			bool isNear = IsTrafficerNearCamera(trafficer, range);
			if (isNear && !trafficer.gameObject.activeSelf)
			{
				trafficer.Show();
			}
			else if (!isNear && trafficer.gameObject.activeSelf)
			{
				trafficer.Hide();
			}
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
	private bool IsTrafficerNearCamera(Trafficer trafficer, float threshold)
	{
		if (CameraController.Instance == null)
		{
			return true; // Nếu không có CameraController, luôn trả về true
		}

		Vector3 cameraPosition = CameraController.Instance.transform.position;
		Vector3 pos = trafficer.GetDestination();
		float dx = Mathf.Abs(pos.x - cameraPosition.x);
		float dz = Mathf.Abs(pos.z - cameraPosition.z);
		// Square (axis-aligned) filter on X and Z axes
		return dx <= threshold && dz <= threshold;
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
