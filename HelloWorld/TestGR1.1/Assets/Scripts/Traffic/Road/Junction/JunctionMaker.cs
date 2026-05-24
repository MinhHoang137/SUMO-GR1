using System.Collections.Generic;
using UnityEngine;

public class JunctionMaker : MonoBehaviour
{
	[SerializeField] private RoadDataSO roadData;
	[SerializeField] private Junction crossRoadPrefab;
	[SerializeField] private JunctionLabel junctionLabelPrefab;

	private Dictionary<string, Junction> junctionMap = new Dictionary<string, Junction>();

	private void Start()
	{
		StartCoroutine(ManipulateAction.Wait(
			() => roadData.junctionDatas == null || roadData.junctionDatas.Count == 0,
			() => CreateJunctions(roadData.junctionDatas)
		));
	}

	private void CreateJunctions(List<JunctionData> crossRoads)
	{
		foreach (var crossRoadData in crossRoads)
		{
			Junction newJunc = CreateJunction(crossRoadData);
			junctionMap.Add(crossRoadData.id, newJunc);
		}
	}

	private Junction CreateJunction(JunctionData junctionData)
	{
		Vector3 position = Converter.ToVector3(junctionData.position);
		Junction junction = Instantiate(crossRoadPrefab, position, Quaternion.identity);
		junction.data = junctionData;
		junction.baseVertices = new List<Vector3>();
		foreach (var vertex in junctionData.vertices)
		{
			Vector3 worldVertex = Converter.ToVector3(vertex) - position;
			junction.baseVertices.Add(worldVertex);
		}
		junction.Create(junction.baseVertices.ToArray(), new Vector3(0, -0.1f, 0), junctionData.id);
		junction.transform.SetParent(transform);
		return junction;
	}

	// ===== OPTIMIZATION (culling theo camera range) =====
	// Tách ra component riêng (xem FilterTransform.cs). Gắn FilterTransform vào prefab Junction
	// nếu muốn ẩn/hiện theo khoảng cách camera. Đoạn dưới giữ lại tham khảo cho phiên bản
	// culling tích hợp sẵn trong maker — không kích hoạt.
	//
	// [Header("Culling")]
	// [SerializeField] private float visibleRange = 1000f;
	//
	// private void Start()
	// {
	//     StartCoroutine(ManipulateAction.Wait(
	//         () => roadData.junctionDatas == null || roadData.junctionDatas.Count == 0,
	//         () =>
	//         {
	//             if (CameraController.Instance != null)
	//             {
	//                 RefreshVisibleJunctions(CameraController.Instance.transform.position);
	//             }
	//         }
	//     ));
	//     if (CameraController.Instance != null)
	//     {
	//         CameraController.Instance.OnCameraMove += HandleCameraMove;
	//     }
	// }
	//
	// private void OnDestroy()
	// {
	//     if (CameraController.Instance != null)
	//     {
	//         CameraController.Instance.OnCameraMove -= HandleCameraMove;
	//     }
	// }
	//
	// private void HandleCameraMove(object sender, System.EventArgs e)
	// {
	//     RefreshVisibleJunctions(CameraController.Instance.transform.position);
	// }
	//
	// private void RefreshVisibleJunctions(Vector3 centerPos)
	// {
	//     foreach (var junctionData in roadData.junctionDatas)
	//     {
	//         if (junctionData == null) continue;
	//         Vector3 junctionPos = new Vector3(junctionData.position[0], 0, junctionData.position[1]);
	//         bool inRange =
	//             junctionPos.x >= centerPos.x - visibleRange &&
	//             junctionPos.x <= centerPos.x + visibleRange &&
	//             junctionPos.z >= centerPos.z - visibleRange &&
	//             junctionPos.z <= centerPos.z + visibleRange;
	//
	//         if (inRange)
	//         {
	//             if (!junctionMap.ContainsKey(junctionData.id))
	//             {
	//                 Junction newJunc = CreateJunction(junctionData);
	//                 junctionMap.Add(junctionData.id, newJunc);
	//             }
	//             else if (!junctionMap[junctionData.id].gameObject.activeSelf)
	//             {
	//                 junctionMap[junctionData.id].gameObject.SetActive(true);
	//             }
	//         }
	//         else if (junctionMap.ContainsKey(junctionData.id))
	//         {
	//             if (junctionMap[junctionData.id].gameObject.activeSelf)
	//                 junctionMap[junctionData.id].gameObject.SetActive(false);
	//         }
	//     }
	// }
}
