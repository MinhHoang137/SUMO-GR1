using UnityEngine;

public class TrafficLight : MonoBehaviour
{
	private const float UNITY_HEIGHT_OFFSET_FROM_SUMO = 4f;
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
		Vector3 position = Converter.ToVector3(data.Position) + Vector3.up * UNITY_HEIGHT_OFFSET_FROM_SUMO;
		Vector3 dir = Converter.ToVector3(data.Direction);
		Vector3 planarDir = new Vector3(dir.x, 0f, dir.z);
		if (planarDir.sqrMagnitude < 1e-6f) planarDir = Vector3.forward;

		transform.position = position;
		transform.forward = -planarDir.normalized;
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
	public void SetPositionFromSumo(Coordinate sumoPosition)
	{
		transform.position = Converter.ToVector3(sumoPosition) + Vector3.up * UNITY_HEIGHT_OFFSET_FROM_SUMO;
	}
}
