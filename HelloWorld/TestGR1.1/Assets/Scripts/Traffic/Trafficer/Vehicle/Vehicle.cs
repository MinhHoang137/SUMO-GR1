using System;
using UnityEngine;

[RequireComponent(typeof(Trafficer))]
public class Vehicle : MonoBehaviour
{
	private Trafficer trafficer;

	public class OnMoveArgs : EventArgs
	{
		public float speed;
		public OnMoveArgs(float speed)
		{
			this.speed = speed;
		}
	}
	public event EventHandler<OnMoveArgs> OnMove;
	protected Vector3 lastPos;

	private void Awake()
	{
		trafficer = GetComponent<Trafficer>();
	}

	private void Start()
	{
		lastPos = transform.position;
	}
	// Update is called once per frame
	void LateUpdate()
	{
		InvokeMove();
	}

	public void Set(TrafficerData vehicleData)
	{
		trafficer.SetId(vehicleData.id);
		trafficer.SetDestination(new Vector3(vehicleData.position[0], 0, vehicleData.position[1]));
		trafficer.SetSpeed(vehicleData.speed);
	}
	protected void InvokeMove()
	{
		Vector3 direction = transform.position - lastPos;
		float deltaDistance = Vector3.Dot(direction, transform.forward);
		OnMove?.Invoke(this, new OnMoveArgs(deltaDistance / Time.deltaTime));
		lastPos = transform.position;
	}
}
