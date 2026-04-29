using System;
using UnityEngine;

public class FilterTransform : MonoBehaviour
{
    [SerializeField] private FilterSO filterSO;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        CameraController.Instance.OnCameraMove += CameraController_OnCameraMove;
        if (filterSO.GetUseFilter())
        {
            Filter();
        }

    }

    private void CameraController_OnCameraMove(object sender, EventArgs e)
    {
        if (filterSO.GetUseFilter())
        {
            Filter();
        } else
        {
            gameObject.SetActive(true);
        }
    }
    private void Filter()
    {
        float distance = Vector3.Distance(transform.position, CameraController.Instance.transform.position);
        if (distance > filterSO.FilterDistance)
        {
            gameObject.SetActive(false);
        }
        else
        {
            gameObject.SetActive(true);
        }
    }
    private void OnDestroy()
    {
        CameraController.Instance.OnCameraMove -= CameraController_OnCameraMove;
    }
}
