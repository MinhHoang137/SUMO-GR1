using UnityEngine;

public class Vehicle : MonoBehaviour
{
    private string id;
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
    private void Move()
    {
        lastPosition = transform.position;
		transform.position = Vector3.Lerp(transform.position, destination, speed * Time.deltaTime);
		//transform.position = Vector3.MoveTowards(transform.position, destination, speed * Time.deltaTime);
		Vector3 direction = destination - lastPosition;
        if (direction != Vector3.zero)
		{
            float multiplier = 10;
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
		this.id = id;
	}
	public string GetId()
	{
		return id;
	}
}
