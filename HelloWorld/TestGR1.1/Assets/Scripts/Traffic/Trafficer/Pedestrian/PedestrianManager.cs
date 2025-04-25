using UnityEngine;
using System.Collections.Generic;

public class PedestrianManager : TrafficerObjectManager<Pedestrian, PedestrianData>
{
    [SerializeField] private PedestrianReader pedestrianReader;
	private void Start()
	{
		StartManager(() =>
		{
			pedestrianReader.OnReadComplete += (sender, args) =>
			{
				ProcessData(args.data);
			};
		});
	}
}
