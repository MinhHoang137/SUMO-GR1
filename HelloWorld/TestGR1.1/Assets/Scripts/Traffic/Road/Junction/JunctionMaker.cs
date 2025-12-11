using UnityEngine;
using System.Collections.Generic;

public class JunctionMaker : MonoBehaviour
{
	[SerializeField] private RoadDataSO roadData;
	[SerializeField] private Junction crossRoadPrefab;
	[SerializeField] private JunctionLabel junctionLabelPrefab;
	private Dictionary<string, Junction> junctionMap = new Dictionary<string, Junction>();
	private float scaleRange = 10f;
	[SerializeField] private bool debugLog = false;
	private void Start()
	{
		StartCoroutine(ManipulateAction.Wait(() => {
			return roadData.junctionDatas == null || roadData.junctionDatas.Count == 0;
		}, () => {
			// After data becomes available, create an initial visible set based on camera
			if (CameraController.Instance != null)
			{
				Vector3 pos = CameraController.Instance.transform.position;
				float defaultMoveThreshold = CameraController.Instance.GetFarDistance(); // matches CameraController default
				List<JunctionData> initial = FiltJunctions(pos, defaultMoveThreshold * scaleRange);
				foreach (var junctionData in initial)
				{
					junctionMap[junctionData.id].gameObject.SetActive(true);
				}
			}
		}));

		CameraController.Instance.OnCameraMove += (sender, e) =>
		{
			List<JunctionData> newJuncs = FiltJunctions(e.Position, e.MoveThreshold * scaleRange);
			foreach (var junctionData in newJuncs)
			{
				junctionMap[junctionData.id].gameObject.SetActive(true);
			}
		};
    }

    /// <summary>
    /// Tìm các junction trong phạm vi range từ centerPos
	///
    /// </summary>
	/// <remarks> Loại bỏ các junction ngoài phạm vi và trả về các junction mới trong phạm vi chưa được tạo </remarks>
    /// <param name="centerPos"> Vị trí trung tâm </param>
    /// <param name="range"> </param>
    /// <returns></returns>
    private List<JunctionData> FiltJunctions(Vector3 centerPos, float range)
	{
		List<JunctionData> newJunctons = new List<JunctionData>();
        foreach (var junctionData in roadData.junctionDatas)
		{
			if (junctionData == null)
			{
				if (debugLog) Debug.LogWarning($"[JunctionMaker] junctionData is null in list");
				continue;
			}
			if (junctionData.position == null || junctionData.position.Length < 2)
			{
				if (debugLog) Debug.LogWarning($"[JunctionMaker] malformed position for junction '{junctionData?.id ?? "(null)"}'");
				continue;
			}
			bool inRange = true;
			Vector3 junctionPos = new Vector3(junctionData.position[0], 0, junctionData.position[1]);
			inRange &= junctionPos.x >= centerPos.x - range;
			inRange &= (junctionPos.x <= centerPos.x + range);
			inRange &= (junctionPos.z >= centerPos.z - range);
			inRange &= (junctionPos.z <= centerPos.z + range);
			if (inRange)
			{
				if (!junctionMap.ContainsKey(junctionData.id))
				{
					Junction newJunc = CreateJunction(junctionData);
					junctionMap.Add(junctionData.id, newJunc);
					newJunctons.Add(junctionData);
					if (debugLog) Debug.Log($"[JunctionMaker] Created junction '{junctionData.id}' at {junctionPos}");
				}
				else
				{
					// already present, ensure active
					if (!junctionMap[junctionData.id].gameObject.activeSelf)
					{
						junctionMap[junctionData.id].gameObject.SetActive(true);
						if (debugLog) Debug.Log($"[JunctionMaker] Re-activated junction '{junctionData.id}'");
					}
				}
			}
			else
			{
				if (junctionMap.ContainsKey(junctionData.id))
				{
					// hide but keep instance in map so it can be re-used without re-instantiation
					junctionMap[junctionData.id].gameObject.SetActive(false);
					if (debugLog) Debug.Log($"[JunctionMaker] Hid junction '{junctionData.id}' (out of range)");
                }
            }
        }
		return newJunctons;
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
