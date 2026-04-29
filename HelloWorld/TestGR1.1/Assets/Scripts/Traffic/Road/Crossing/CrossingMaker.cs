using System.Collections.Generic;
using UnityEngine;

public class CrossingMaker : MonoBehaviour
{
	[SerializeField] private Crossing crossingPrefab;
	[SerializeField] private RoadDataSO roadData;
	private Dictionary<string, Crossing> crossingMap = new Dictionary<string, Crossing>();
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
	{
		StartCoroutine(ManipulateAction.Wait(() =>
		{
			return roadData.crossingDatas == null || roadData.crossingDatas.Count == 0;
		}, () =>
		{
			CreateCrossings();
		}));
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
}
