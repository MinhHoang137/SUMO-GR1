using UnityEngine;
using UnityEngine.UI;

public class SimulationEndUI : MonoBehaviour
{
    [SerializeField] private Button closeButton;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        if (closeButton != null)
            closeButton.onClick.AddListener(OnCloseButtonClicked);
    }
    public void OnCloseButtonClicked()
    {
        Application.Quit();
    }
   
}
