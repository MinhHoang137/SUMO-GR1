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

	private string lastJson = ""; // Tránh đọc dữ liệu lặp lại

	private List<TrafficerData> trafficers;

	private void Awake()
	{
		Instance = this;
	}
	//private void Start()
	//{
	//	string fullPath = Path.GetFullPath(filePath);
	//	Debug.Log("Đường dẫn đầy đủ: " + fullPath);
	//}
	void Update()
	{
		if (File.Exists(lockFilePath))
		{
			Debug.Log("File lock tồn tại, đợi Python ghi xong...");
			return;
		}
		ReadJsonData();
	}

	void ReadJsonData()
	{
		if (!File.Exists(filePath))
		{
			Debug.LogError("File không tồn tại: " + filePath);
			return;
		}
		// Đọc file JSON với quyền chia sẻ để Python vẫn có thể ghi
		using (FileStream fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
		using (StreamReader sr = new StreamReader(fs))
		{
			string jsonContent = sr.ReadToEnd();
			// Kiểm tra nếu dữ liệu không thay đổi thì không parse lại
			if (jsonContent == lastJson) return;
			lastJson = jsonContent;
			//Debug.Log(jsonContent);

			trafficers = JsonConvert.DeserializeObject<List<TrafficerData>>(jsonContent);
			OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs { trafficers = this.trafficers });
		}
	}
}
