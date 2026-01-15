using System;
using UnityEngine;

public class Vehicle: Trafficer
{
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

	private void Start()
	{
		lastPos = transform.position;
	}
	// Update is called once per frame
	void Update()
    {
        Move();
	}
	protected override void Move()
	{
		base.Move();
		InvokeMove();
	}
	public void Set(VehicleData vehicleData)
	{
		SetId(vehicleData.id);
		SetDestination(Converter.ToVector3(vehicleData.position));
		SetSpeed(vehicleData.speed);
	}
	protected void InvokeMove()
	{
		Vector3 direction = transform.position - lastPos;
		float deltaDistance = Vector3.Dot(direction, transform.forward);
		OnMove?.Invoke(this, new OnMoveArgs(deltaDistance / Time.deltaTime));
		lastPos = transform.position;
	}
}
