using System;

[Serializable]
public class TrafficerData: ObjectData
{
	public string id;
	public float[] position;
	public float speed;
	public float[] forward;
	public TrafficerData(string id, string type, float[] position, float[] forward, float speed, string lane)
	{
		this.id = id;
		this.type = type;
		this.position = position;
		this.speed = speed;
		this.forward = forward;
	}
}