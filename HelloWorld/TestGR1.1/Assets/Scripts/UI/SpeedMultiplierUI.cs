using UnityEngine;

public class SpeedMultiplierUI : MonoBehaviour
{
    [SerializeField] private ValueUI speedMultiplierValueUI;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        speedMultiplierValueUI.Create((value) =>
		{
			SpeedMultiplier.Instance.Multiplier = value;
		});
	}
	private void OnDestroy()
	{
		speedMultiplierValueUI.Destroy();
	}
}
