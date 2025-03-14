using System.Xml.Serialization;
using UnityEngine;

public abstract class Trafficer : MonoBehaviour
{
    private string id = null;
	private Vector3 destination;
	private float speed;
    private Vector3 lastPosition;

	public bool isExist = true;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        Move();
    }
    protected void Move()
    {
		lastPosition = transform.position;
		transform.position = Vector3.Lerp(transform.position, destination, speed * Time.deltaTime);
		//transform.position = Vector3.MoveTowards(transform.position, destination, speed * Time.deltaTime);
		Vector3 direction = destination - lastPosition;
        if (direction != Vector3.zero)
		{
            float multiplier = 5;
			transform.forward = Vector3.Slerp(transform.forward, direction, speed * Time.deltaTime * multiplier);
		}
	}
	public void SetDestination(Vector3 destination)
	{
		this.destination = destination;
	}
	public void SetSpeed(float speed)
	{
		this.speed = speed;
	}
	public void SetId(string id)
	{
		if (this.id == null) this.id = id;
	}
	public string GetId()
	{
		return id;
	}
	public void Set(TrafficerData trafficerData)
	{
		SetId(trafficerData.id);
		SetDestination(new Vector3(trafficerData.position[0], 0, trafficerData.position[1]));
		SetSpeed(trafficerData.speed);
	}
}
