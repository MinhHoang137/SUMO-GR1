using System.IO;
using UnityEngine;
using System;
using System.Collections.Generic;
using Newtonsoft.Json;

public class JunctionReader : MonoBehaviour
{
	public static JunctionReader Instance { get; private set; }
	public class OnReadCompleteEventArgs : EventArgs
	{
		public List<JunctionData> crossRoads;
	}
	public event EventHandler<OnReadCompleteEventArgs> OnReadComplete;
	private string filePath;
	private List<JunctionData> crossroadData;
	private void Awake()
	{
		Instance = this;
	}
	private void Start()
	{
		filePath = Path.Combine(Application.dataPath, "Scripts/SumoData/CrossRoad.json");
		Read();
	}
	private void Read()
	{
		string jsonText = File.ReadAllText(filePath);
		// Chuyển đổi JSON sang đối tượng C# với Newtonsoft.Json
		crossroadData = JsonConvert.DeserializeObject<List<JunctionData>>(jsonText);
		//Debug.Log(jsonText);
		if (OnReadComplete != null)
		{
			OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs { crossRoads = crossroadData });
			//Debug.Log("Sự kiện OnReadComplete đã được gọi");
		}
		else
		{
			Debug.LogError("Sự kiện OnReadComplete không có listener nào được đăng ký");
		}

	}
}
