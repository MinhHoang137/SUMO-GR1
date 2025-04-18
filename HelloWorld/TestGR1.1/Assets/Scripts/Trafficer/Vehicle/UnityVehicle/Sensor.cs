using UnityEngine;

public class Sensor : MonoBehaviour
{
    protected bool canMove = true;
	public virtual bool CanMove()
	{
		return canMove;
	}
}
