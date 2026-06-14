using UnityEngine;

public class CarCollisionIcon : MonoBehaviour
{
    [SerializeField] private Trafficer vehicle;

    private void OnEnable()
    {
        if (vehicle != null)
        {
            gameObject.SetActive(vehicle.existState == ExistState.Wrecked);
        }
    }
}
