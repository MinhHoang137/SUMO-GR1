using UnityEngine;
using System.Collections.Generic;

public class JunctionMaker : MonoBehaviour
{
	[SerializeField] private RoadDataSO roadData;
	[SerializeField] private Junction crossRoadPrefab;
	[SerializeField] private JunctionLabel junctionLabelPrefab;
	private Dictionary<string, Junction> junctionMap = new Dictionary<string, Junction>();

	private void Start()
	{
		StartCoroutine(ManipulateAction.Wait(() => {
			return roadData.junctionDatas == null || roadData.junctionDatas.Count == 0;
		}, () => {
			CreateJunctions(roadData.junctionDatas);
		}));
    }

	private Junction CreateJunction(JunctionData junctionData)
	{
		Vector3 position = Converter.ToVector3(junctionData.position);
		Junction junction = Instantiate(crossRoadPrefab, position, Quaternion.identity);
		junction.baseVertices = new List<Vector3>();
		foreach (var vertex in junctionData.vertices)
		{
			Vector3 worldVertex = new Vector3(vertex.x, 0, vertex.y) - position;
			junction.baseVertices.Add(worldVertex);
		}
		junction.Create(junction.baseVertices.ToArray(), new Vector3(0, -1, 0), junctionData.id);
		junction.transform.SetParent(transform);
		return junction;
    }
    private void CreateJunctions(List<JunctionData> crossRoads)
	{
		foreach (var crossRoadData in crossRoads)
		{
			Junction newJunc = CreateJunction(crossRoadData);
			junctionMap.Add(crossRoadData.id, newJunc);
            // Create label
            // JunctionLabel label = Instantiate(junctionLabelPrefab, Vector3.zero, Quaternion.identity);
            // label.SetText(crossRoadData.id);
            // label.transform.SetParent(crossRoad.transform);
            // label.transform.localPosition = Converter.ToVector3(crossRoadData.position);
        }
	}

}
