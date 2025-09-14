using UnityEngine;
using System.Collections.Generic;

public class PedestrianManager : TrafficerObjectManager<Pedestrian, PedestrianData>
{


	public static PedestrianManager Instance { get; private set; }

	private void Awake()
	{
		if (Instance == null)
		{
			Instance = this;
		}
	}

	private void Start()
	{
		StartManager(() =>
		{
		});
	}
	private void OnDestroy()
	{
		if (Instance == this)
		{
			Instance = null;
		}
	}
}
