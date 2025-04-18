using UnityEngine;
using System.Collections.Generic;

public class PedestrianManager : MonoBehaviour
{
    [SerializeField] private PedestrianReader pedestrianReader;
	[SerializeField] private Pedestrian[] pedestrianPrefabs;
	private Dictionary<string, Pedestrian> pedestrianDict = new Dictionary<string, Pedestrian>();
	private void Start()
	{
		pedestrianReader.OnReadComplete += (sender, args) =>
		{
			List<Pedestrian> pedestrianList = new List<Pedestrian>(pedestrianDict.Values);
			foreach (var pedestrian in pedestrianList)
			{
				pedestrian.isExist = false;
			}
			foreach (var data in args.data)
			{
				if (pedestrianDict.TryGetValue(data.id, out Pedestrian pedestrian))
				{
					pedestrian.Set(data);
					pedestrian.isExist = true;
				}
				else
				{
					SpawnPedestrian(data);
				}
			}
			try
			{
				foreach (var pedestrian in pedestrianList)
				{
					if (!pedestrian.isExist)
					{
						DestroyPedestrian(pedestrian);
					}
				}
			}
			catch (System.InvalidOperationException e)
			{
				Debug.Log(e);
			}
		};
	}
	private void SpawnPedestrian(PedestrianData data)
	{
		int index = Random.Range(0, pedestrianPrefabs.Length);
		Vector3 position = new Vector3(data.position[0], 0, data.position[1]);
		Pedestrian pedestrian = Instantiate(pedestrianPrefabs[index], position, Quaternion.identity);
		pedestrian.transform.forward = new Vector3(data.forward[0], 0, data.forward[1]);
		pedestrian.Set(data);
		pedestrianDict.Add(data.id, pedestrian);
		TrafficerManager.Instance.AddTrafficer(pedestrian);
		pedestrian.transform.SetParent(transform);
	}
	private void DestroyPedestrian(Pedestrian p)
	{
		pedestrianDict.Remove(p.GetId());
		Destroy(p.gameObject);
		TrafficerManager.Instance.RemoveTrafficer(p);
	}
}
