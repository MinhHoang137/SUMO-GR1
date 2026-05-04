using UnityEngine;

[RequireComponent(typeof(Trafficer))]
public class Pedestrian : MonoBehaviour
{
    public Trafficer Trafficer { get; private set; }

    private void Awake()
    {
        Trafficer = GetComponent<Trafficer>();
    }
}
