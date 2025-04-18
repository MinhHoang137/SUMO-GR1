using System;

[Serializable]
public class TrafficerData
{
	public string id;
	public string type;
	public float[] position;
	public float[] forward;
	public float speed;
	public string lane;
	public TrafficerData(string id, string type, float[] position, float[] forward, float speed, string lane)
	{
		this.id = id;
		this.type = type;
		this.position = position;
		this.forward = forward;
		this.speed = speed;
		this.lane = lane;
	}
}