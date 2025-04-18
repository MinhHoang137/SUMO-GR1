using UnityEngine;

public class SpeedMultiplier : MonoBehaviour
{
	public static SpeedMultiplier Instance { get; private set; }
	[SerializeField] private float speedMultiplier = 1.0f;
    public float Multiplier
	{
		get { return speedMultiplier; }
	}
	private void Awake()
	{
		Instance = this;
	}
}
