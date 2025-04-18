using UnityEngine;

public class Wheel : MonoBehaviour
{
    [SerializeField] private Vehicle car;
	[SerializeField] private float radius = 0.3456101f;
	[SerializeField] private float deltaAngle = 0;
	public enum RotateDirection
	{
		Clockwise, CounterClockwise
	}
	[SerializeField] private RotateDirection rotateDirection;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        car.OnMove += (sender, args) =>
		{
			deltaAngle = args.speed * Time.deltaTime / (2 * Mathf.PI * radius) * 360;
			if (rotateDirection == RotateDirection.Clockwise)
			{
				transform.Rotate(new Vector3(deltaAngle, 0, 0));
			}
			else
			{
				transform.Rotate(new Vector3(-deltaAngle, 0, 0));
			}
		};
	}
}
