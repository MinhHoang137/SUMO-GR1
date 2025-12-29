using UnityEngine;

public class SpeedMultiplierUI : MonoBehaviour
{
    [SerializeField] private ValueUI speedMultiplierValueUI;
	private float value;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        speedMultiplierValueUI.Create((value) =>
		{
			SpeedMultiplier.Instance.Multiplier = value;
			this.value = value;
		});
	}

	public void SetValue(float value)
	{
		if (value < 0.01f)
		{
			value = 0.01f;
		}
		speedMultiplierValueUI.SetValue(value);
		this.value = value;
	}

    public void ScaleValueInversely(float ratio)
    {
        if (ratio == 0) return;
        SetValue(this.value / ratio);
    }

	public float GetValue()
	{
		return this.value;
	}

	private void OnDestroy()
	{
		speedMultiplierValueUI.Destroy();
	}
}
