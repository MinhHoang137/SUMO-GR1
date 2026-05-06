using System;

[Serializable]
public class UnityVehicleData
{
	public string id;
	public float[] position;
	public float[] forward;
	public float speed;
	public bool isExist;

	public UnityVehicleData(string id, float[] position, float[] forward, float speed, bool isExist = true)
	{
		this.id = id;
		this.position = position;
		this.forward = forward;
		this.speed = speed;
		this.isExist = isExist;
	}
}
