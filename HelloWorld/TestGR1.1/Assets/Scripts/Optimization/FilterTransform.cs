using System;
using UnityEngine;

public class FilterTransform : MonoBehaviour
{
    [SerializeField] private FilterSO filterSO;

    void Start()
    {
        EnableFilter();
    }

    public void EnableFilter()
    {
        if (CameraController.Instance == null) return;
        CameraController.Instance.OnCameraMove -= CameraController_OnCameraMove; // chống đăng ký trùng
        CameraController.Instance.OnCameraMove += CameraController_OnCameraMove;
        if (filterSO != null && filterSO.GetUseFilter()) Filter();
    }

    public void DisableFilter()
    {
        if (CameraController.Instance != null)
            CameraController.Instance.OnCameraMove -= CameraController_OnCameraMove;
    }

    private void CameraController_OnCameraMove(object sender, EventArgs e)
    {
        if (filterSO.GetUseFilter())
            Filter();
        else
            gameObject.SetActive(true);
    }

    private void Filter()
    {
        float disX = Mathf.Abs(transform.position.x - CameraController.Instance.transform.position.x);
        float disZ = Mathf.Abs(transform.position.z - CameraController.Instance.transform.position.z);
        gameObject.SetActive(disX <= filterSO.FilterDistance && disZ <= filterSO.FilterDistance);
    }

    private void OnDestroy()
    {
        DisableFilter();
    }
}
