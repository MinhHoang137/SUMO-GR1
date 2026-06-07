using UnityEngine;
using TMPro;
using System;

public class LatencyText : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI latencyText;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        if (TrafficerManager.Instance != null)
        {
            TrafficerManager.Instance.OnLatencyChanged += TrafficManager_OnLatencyChanged;
        }
    }

    private void TrafficManager_OnLatencyChanged(object sender, TrafficerManager.LatencyEventArgs e)
    {
        if (latencyText != null)
        {
            latencyText.text = $"Độ trễ: {e.LatencyMs} ms";
        }
    }

    private void OnDestroy()
    {
        if (TrafficerManager.Instance != null)
        {
            TrafficerManager.Instance.OnLatencyChanged -= TrafficManager_OnLatencyChanged;
        }
    }

}
