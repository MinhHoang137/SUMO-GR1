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
		Junction junction = Instantiate(crossRoadPrefab, Vector3.zero, Quaternion.identity);
		junction.baseVertices = new List<Vector3>();
		foreach (var vertex in junctionData.vertices)
		{
			junction.baseVertices.Add(new Vector3(vertex.x, 0, vertex.y));
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
