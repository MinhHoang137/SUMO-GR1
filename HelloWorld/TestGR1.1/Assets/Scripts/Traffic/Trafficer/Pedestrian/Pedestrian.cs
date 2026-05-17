using UnityEngine;

[RequireComponent(typeof(Trafficer))]
public class Pedestrian : MonoBehaviour
{
    public Trafficer Trafficer { get; private set; }

    private void Awake()
    {
        Trafficer = GetComponent<Trafficer>();
    }
    public float GetFullSpeed()
    {
        return Trafficer.GetFullSpeed();
    }
    public float GetBaseSpeed()
    {
        return Trafficer.GetBaseSpeed();
    }
}
