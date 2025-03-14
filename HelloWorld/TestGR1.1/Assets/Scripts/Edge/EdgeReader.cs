using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Newtonsoft.Json;
using System;

public class EdgeReader : MonoBehaviour
{
	public class OnReadCompleteEventArgs: EventArgs
	{
		public List<EdgeData> edges;
	}
	public event EventHandler<OnReadCompleteEventArgs> OnReadComplete;
	private string filePath;
    private List<EdgeData> edges;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        filePath = Application.dataPath + "/Scripts/SumoData/Edge.json";
		StartCoroutine(DelayAction.Delay(() =>
		{
			Read();
		}, Time.deltaTime));
	}
    private void Read()
	{
		if (!File.Exists(filePath))
		{
			Debug.LogError("File not found: " + filePath);
			return;
		}
		string jsonText = File.ReadAllText(filePath);
		//Debug.Log(jsonText);
		edges = JsonConvert.DeserializeObject<List<EdgeData>>(jsonText);
		OnReadComplete?.Invoke(this, new OnReadCompleteEventArgs { edges = this.edges });
	}
}
