using UnityEngine;

/// <summary>
/// Cầu nối giữa FilterTransform và vòng đời trafficer.
/// Khi trafficer bị recycle → DisableFilter (ngắt camera event, tránh xe ma).
/// Khi trafficer được spawn lại → EnableFilter (bật lại).
/// Gắn cùng GameObject với FilterTransform và Trafficer.
/// </summary>
[RequireComponent(typeof(FilterTransform))]
[RequireComponent(typeof(Trafficer))]
public class FilterTrafficer : MonoBehaviour
{
    private FilterTransform filterTransform;
    private Trafficer trafficer;

    private void Awake()
    {
        filterTransform = GetComponent<FilterTransform>();
        trafficer = GetComponent<Trafficer>();
    }

    private void OnEnable()
    {
        if (TrafficerManager.Instance != null)
        {
            TrafficerManager.Instance.OnRemoveTrafficer += OnRemoveTrafficer;
            TrafficerManager.Instance.OnAddTrafficer    += OnAddTrafficer;
        }
    }

    private void OnDisable()
    {
        if (TrafficerManager.Instance != null)
        {
            TrafficerManager.Instance.OnRemoveTrafficer -= OnRemoveTrafficer;
            TrafficerManager.Instance.OnAddTrafficer    -= OnAddTrafficer;
        }
    }

    private void OnRemoveTrafficer(object sender, TrafficerManager.TrafficerEventArgs e)
    {
        if (e.Trafficer == trafficer) filterTransform.DisableFilter();
    }

    private void OnAddTrafficer(object sender, TrafficerManager.TrafficerEventArgs e)
    {
        if (e.Trafficer == trafficer) filterTransform.EnableFilter();
    }
}
