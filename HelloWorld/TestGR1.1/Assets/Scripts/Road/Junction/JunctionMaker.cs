using UnityEngine;
using System.Collections.Generic;

public class JunctionMaker : MonoBehaviour
{
	[SerializeField] private RoadData roadData;
	[SerializeField] private Junction crossRoadPrefab;
	private void Start()
	{
		StartCoroutine(ManipulateAction.Wait(() => {
			return roadData.junctionDatas == null || roadData.junctionDatas.Count == 0;
		}, () => {
			CreateJunction(roadData.junctionDatas);
		}));
	}
	private void CreateJunction(List<JunctionData> crossRoads)
	{
		foreach (var crossRoadData in crossRoads)
		{
			Junction crossRoad = Instantiate(crossRoadPrefab, Vector3.zero, Quaternion.identity);
			crossRoad.baseVertices = new List<Vector3>();
			foreach (var vertex in crossRoadData.vertices)
			{
				crossRoad.baseVertices.Add(new Vector3(vertex.x, 0, vertex.y));
			}
			crossRoad.Create(crossRoad.baseVertices.ToArray(), new Vector3(0, -1, 0), crossRoadData.id);
			crossRoad.transform.SetParent(transform);
		}
	}
}
