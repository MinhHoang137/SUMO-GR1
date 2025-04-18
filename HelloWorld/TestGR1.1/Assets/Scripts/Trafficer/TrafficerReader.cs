using Newtonsoft.Json;
using System.Collections.Generic;
using System.IO;
using System;
using UnityEngine;

public class TrafficerReader : MonoBehaviour
{
	public static TrafficerReader Instance { get; private set; }

	public class OnReadCompleteEventArgs : EventArgs
	{
		public List<TrafficerData> trafficers;
	}
	public event EventHandler<OnReadCompleteEventArgs> OnReadComplete;

	private string filePath = Path.Combine(Application.dataPath, "Scripts/SumoData/HelloWorld.json");
	private string lockFilePath = Path.Combine(Application.dataPath, "Scripts/SumoData/lock.tmp");
	private string lastJson = "";

	private void Awake()
	{
		Instance = this;
	}

	void Update()
	{
		if (File.Exists(lockFilePath))
		{
			Debug.Log("Waiting for Python to finish writing...");
			return;
		}
		ReadJsonData();
	}

	void ReadJsonData()
	{
		if (!File.Exists(filePath))
		{
			Debug.LogError("File not found: " + filePath);
			return;
		}

		using (FileStream fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
		using (StreamReader sr = new StreamReader(fs))
		{
			string jsonContent = sr.ReadToEnd();
			if (jsonContent == lastJson) return;
			lastJson = jsonContent;

			List<TrafficerData> trafficers = JsonConvert.DeserializeObject<List<TrafficerData>>(jsonContent);
			OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs { trafficers = trafficers });
		}
	}
}