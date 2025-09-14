using System;

[Serializable]
public class VehicleData : TrafficerData
{
	public bool turnLeft;
	public bool turnRight;
	public bool isBraking;
	public VehicleData(string id, string type, float[] 
		position, float[] forward, float speed, string lane, 
		bool turnLeft, bool turnRight, bool isBraking) 
		: base(id, type, position, forward, speed, lane)
	{
		this.turnLeft = turnLeft;
		this.turnRight = turnRight;
		this.isBraking = isBraking;
	}
}
