using System.Collections.Generic;
using UnityEngine;

public class EdgeMaker : MonoBehaviour
{
	[SerializeField] private Edge edgePrefab;
	[SerializeField] private RoadDataSO roadData;
	private Dictionary<string, Edge> edgeMap = new Dictionary<string, Edge>();
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		StartCoroutine(ManipulateAction.Wait(() =>
		{
			return roadData.edgeDatas == null || roadData.edgeDatas.Count == 0;
		}, () =>
		{
			CreateEdges();
		}));
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
}
