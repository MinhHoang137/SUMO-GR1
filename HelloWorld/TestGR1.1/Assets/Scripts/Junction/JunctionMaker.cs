using UnityEngine;
using System.Collections.Generic;

public class JunctionMaker : MonoBehaviour
{
	[SerializeField] private Junction crossRoadPrefab;
	private void Start()
	{
		JunctionReader.Instance.OnReadComplete += OnReadCrossroadComplee;
	}

	private void OnReadCrossroadComplee(object sender, JunctionReader.OnReadCompleteEventArgs e)
	{
		//Debug.Log("Tao nga tu" + e.crossRoads.Count);
		foreach (var crossRoadData in e.crossRoads)
		{
			Junction crossRoad = Instantiate(crossRoadPrefab, Vector3.zero, Quaternion.identity);
			crossRoad.baseVertices = new List<Vector3>();
			foreach (var vertex in crossRoadData.vertices)
			{
				crossRoad.baseVertices.Add(new Vector3(vertex.x, 0, vertex.y));
			}
			crossRoad.Create(crossRoad.baseVertices.ToArray(), new Vector3(0, -1, 0), crossRoadData.id);
		}
	}
}
