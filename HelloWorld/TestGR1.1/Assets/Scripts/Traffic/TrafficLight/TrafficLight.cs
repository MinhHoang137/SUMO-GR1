using UnityEngine;

public class TrafficLight : MonoBehaviour
{
    private const int RED = 0;
	private const int YELLOW = 1;
    private const int GREEN = 2;
    [SerializeField] private GameObject redLight;
    [SerializeField] private GameObject greenLight;
    [SerializeField] private GameObject yellowLight;

    private string id;

    public void Create(TrafficLightData data)
	{
		id = data.Id;
		transform.position = Converter.ToVector3(data.Position);
		// Đèn quay về hướng đối diện với hướng đi của làn (đối diện dòng xe tới).
		transform.forward = -Converter.ToVector3(data.Direction);
		SetState(data.CurrentState);
	}
    public void SetState(int state)
    {
		//Debug.Log("SetState: " + state);
		redLight.SetActive(state == RED);
		yellowLight.SetActive(state == YELLOW);
		greenLight.SetActive(state == GREEN);
	}
	public void SetPosition(Vector3 position)
	{
		transform.position = position;
	}
}
