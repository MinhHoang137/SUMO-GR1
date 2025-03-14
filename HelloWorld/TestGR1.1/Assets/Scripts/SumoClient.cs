﻿using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;
using Newtonsoft.Json;

public class SumoClient : MonoBehaviour
{
	public static SumoClient Instance { get; private set; }
	public class OnReadCompleteEventArgs : EventArgs
	{
		public List<CarData> vehicles;
	}
	public event EventHandler<OnReadCompleteEventArgs> OnReadComplete;

	private string filePath = Path.Combine(Application.dataPath, "Scripts/SumoData/HelloWorld.txt");


	private string lockFilePath = Path.Combine(Application.dataPath, "Scripts/SumoData/lock.tmp");

	private string lastJson = ""; // Tránh đọc dữ liệu lặp lại

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

		try
		{
			// Đọc file JSON với quyền chia sẻ để Python vẫn có thể ghi
			using (FileStream fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
			using (StreamReader sr = new StreamReader(fs))
			{
				string jsonContent = sr.ReadToEnd();
				// Kiểm tra nếu dữ liệu không thay đổi thì không parse lại
				if (jsonContent == lastJson) return;
				lastJson = jsonContent;
				//Debug.Log(jsonContent);
				List<CarData> vehicles = JsonConvert.DeserializeObject<List<CarData>>(jsonContent);
				OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs { vehicles = vehicles });
			}
		}
		catch (Exception e)
		{
			Debug.LogError("Lỗi khi đọc JSON: " + e.Message);
		}
	}
}