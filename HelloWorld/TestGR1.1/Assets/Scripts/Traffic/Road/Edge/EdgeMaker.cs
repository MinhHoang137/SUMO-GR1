using System.Collections.Generic;
using UnityEngine;

public class EdgeMaker : MonoBehaviour
{
	[SerializeField] private Edge edgePrefab;
	[SerializeField] private RoadDataSO roadData;
	private Dictionary<string, Edge> edgeMap = new Dictionary<string, Edge>();
	private float sc = 10f;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		StartCoroutine(ManipulateAction.Wait(() =>
		{
			return roadData.edgeDatas == null || roadData.edgeDatas.Count == 0;
		}, () =>
		{
			// Initially create a small visible set based on camera position
			if (CameraController.Instance != null)
			{
				var pos = CameraController.Instance.transform.position;
				List<EdgeData> initial = FiltEdges(pos, CameraController.Instance != null ? CameraController.Instance.GetType().GetProperty("moveThreshold") == null ? 0f : 0f : 0f);
				// fallback: create none here; creation will be handled by camera move events
			}
		}));

		// Subscribe to camera movement events to show/hide edges dynamically
		if (CameraController.Instance != null)
		{
			CameraController.Instance.OnCameraMove += (sender, e) =>
			{
				List<EdgeData> newEdges = FiltEdges(e.Position, e.MoveThreshold * sc);
				foreach (var edgeData in newEdges)
				{
					edgeMap[edgeData.id].gameObject.SetActive(true);
				}
			};
		}
	}
	private void CreateEdges()
	{
		foreach (EdgeData edgeData in roadData.edgeDatas)
		{
			Edge edge = Instantiate(edgePrefab);
			edge.Create(edgeData);
			edge.transform.SetParent(transform);
			edgeMap[edgeData.id] = edge;
		}
	}

	private List<EdgeData> FiltEdges(Vector3 centerPos, float range)
	{
		List<EdgeData> newEdges = new List<EdgeData>();
		foreach (var edgeData in roadData.edgeDatas)
		{
			bool inRange = true;
			Vector3 edgePos = Converter.ToVector3(edgeData.position);
			inRange &= edgePos.x >= centerPos.x - range;
			inRange &= edgePos.x <= centerPos.x + range;
			inRange &= edgePos.z >= centerPos.z - range;
			inRange &= edgePos.z <= centerPos.z + range;
			if (inRange)
			{
				if (!edgeMap.ContainsKey(edgeData.id))
				{
					Edge newEdge = CreateEdge(edgeData);
					edgeMap.Add(edgeData.id, newEdge);
					newEdges.Add(edgeData);
				}
			}
			else
			{
				if (edgeMap.ContainsKey(edgeData.id))
				{
					edgeMap[edgeData.id].gameObject.SetActive(false);
					edgeMap.Remove(edgeData.id);
				}
			}
		}
		return newEdges;
	}

	private Edge CreateEdge(EdgeData edgeData)
	{
		Edge edge = Instantiate(edgePrefab);
		edge.Create(edgeData);
		edge.transform.SetParent(transform);
		return edge;
	}
}
