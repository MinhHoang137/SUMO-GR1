using System;
using UnityEngine;

/// <summary>
/// Cầu nối giữa FilterTransform và vòng đời trafficer.
/// Khi trafficer bị recycle → DisableFilter (ngắt camera event, tránh xe ma).
/// Khi trafficer được spawn lại → EnableFilter (bật lại).
/// Khi destination đổi lúc đang ẩn → snap transform.position rồi re-check filter,
/// đảm bảo xe vào vùng camera được hiện ra đúng dù chưa từng được render.
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
        trafficer.OnDestinationChanged += Trafficer_OnDestinationChanged;
        if (TrafficerManager.Instance != null)
        {
            TrafficerManager.Instance.OnRemoveTrafficer += OnRemoveTrafficer;
            TrafficerManager.Instance.OnAddTrafficer    += OnAddTrafficer;
        }
    }

    private void OnDisable()
    {
        trafficer.OnDestinationChanged -= Trafficer_OnDestinationChanged;
        if (TrafficerManager.Instance != null)
        {
            TrafficerManager.Instance.OnRemoveTrafficer -= OnRemoveTrafficer;
            TrafficerManager.Instance.OnAddTrafficer    -= OnAddTrafficer;
        }
    }

    private void Trafficer_OnDestinationChanged(object sender, EventArgs e)
    {
        if (gameObject.activeSelf) return;
        // Xe đang ẩn: transform.position bị đóng băng nên FilterTransform.Filter() sẽ check sai.
        // Snap về destination hiện tại trước, rồi để FilterTransform quyết định có hiện không.
        transform.position = trafficer.GetDestination();
        filterTransform.EnableFilter();
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
