using UnityEngine;
using TMPro;

public class TrafficerCountUI : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI carCountText;
    [SerializeField] private TextMeshProUGUI pedestrianCountText;

    // Update is called once per frame
    void Update()
    {
        carCountText.text = $"Số xe: {TrafficerManager.Instance.CarCount}";
        pedestrianCountText.text = $"Số người: {TrafficerManager.Instance.PedestrianCount}";  
    }
}
