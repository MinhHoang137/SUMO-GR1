using System.Collections.Generic;
using UnityEngine;

public class CrossingMaker : MonoBehaviour
{
	[SerializeField] private Crossing crossingPrefab;
	[SerializeField] private RoadDataSO roadData;
	private Dictionary<string, Crossing> crossingMap = new Dictionary<string, Crossing>();
	private float scaleRange = 10;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
	{
		StartCoroutine(ManipulateAction.Wait(() =>
		{
			return roadData.crossingDatas == null || roadData.crossingDatas.Count == 0;
		}, () =>
		{
			// Do not create all crossings at once; initial creation will happen on camera move
		}));

		if (CameraController.Instance != null)
		{
			CameraController.Instance.OnCameraMove += (sender, e) =>
			{
				List<CrossingData> newCrossings = FiltCrossings(e.Position, e.MoveThreshold * scaleRange);
				foreach (var crossingData in newCrossings)
				{
					crossingMap[crossingData.id].gameObject.SetActive(true);
				}
			};
		}
	}
	private void CreateCrossings()
	{
		foreach (var crossingData in roadData.crossingDatas)
		{
			Crossing crossing = Instantiate(crossingPrefab);
			crossing.Create(crossingData);
			crossing.transform.SetParent(this.transform);
			crossingMap[crossingData.id] = crossing;
		}
	}

	private List<CrossingData> FiltCrossings(Vector3 centerPos, float range)
	{
		List<CrossingData> newCross = new List<CrossingData>();
		foreach (var crossingData in roadData.crossingDatas)
		{
			bool inRange = true;
			Vector3 start = new Vector3(crossingData.start.x, 0, crossingData.start.y);
			Vector3 end = new Vector3(crossingData.end.x, 0, crossingData.end.y);
			Vector3 mid = (start + end) / 2f;
			inRange &= mid.x >= centerPos.x - range;
			inRange &= mid.x <= centerPos.x + range;
			inRange &= mid.z >= centerPos.z - range;
			inRange &= mid.z <= centerPos.z + range;
			if (inRange)
			{
				if (!crossingMap.ContainsKey(crossingData.id))
				{
					Crossing newC = CreateCrossing(crossingData);
					crossingMap.Add(crossingData.id, newC);
					newCross.Add(crossingData);
				}
			}
			else
			{
				if (crossingMap.ContainsKey(crossingData.id))
				{
					crossingMap[crossingData.id].gameObject.SetActive(false);
					crossingMap.Remove(crossingData.id);
				}
			}
		}
		return newCross;
	}

	private Crossing CreateCrossing(CrossingData crossingData)
	{
		Crossing crossing = Instantiate(crossingPrefab);
		crossing.Create(crossingData);
		crossing.transform.SetParent(this.transform);
		return crossing;
	}
}
