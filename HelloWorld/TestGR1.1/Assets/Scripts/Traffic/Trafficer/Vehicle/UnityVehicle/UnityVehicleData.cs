using UnityEngine;

public class UnityVehicleData : VehicleData
{
    public bool isExist;
	public UnityVehicleData(string id, string type,
		float[] position, float[] forward, float speed,
		string lane, bool turnLeft, bool turnRight, 
		bool isBraking, bool isExist) : base(id, type, 
			position, forward, speed, lane, turnLeft, turnRight, isBraking)
	{
		this.isExist = isExist;
	}
}
