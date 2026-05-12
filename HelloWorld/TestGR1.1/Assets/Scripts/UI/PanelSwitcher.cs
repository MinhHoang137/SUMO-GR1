using System;
using UnityEngine;
using UnityEngine.UI;

[Serializable]
public struct Button_Panel
{
    public Button button;
    public GameObject panel;
}

public class PanelSwitcher : MonoBehaviour
{
    [SerializeField] private Button_Panel[] buttonPanels;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        foreach (var buttonPanel in buttonPanels){
            buttonPanel.button.onClick.AddListener(() =>
            {
                foreach (var bp in buttonPanels)
                {
                   bp.panel.SetActive(false); // Đóng tất cả bảng trước khi mở bảng yêu cầu
                }
                buttonPanel.panel.SetActive(true); // Mở bảng yêu cầu
            });
        }
    }

}
