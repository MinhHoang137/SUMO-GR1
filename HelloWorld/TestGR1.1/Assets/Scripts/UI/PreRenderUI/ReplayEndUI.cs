using UnityEngine;
using UnityEngine.UI;

public class ReplayEndUI : MonoBehaviour
{
    [SerializeField] private Button closeAppButton;
    [SerializeField] private Button restartButton;
    [SerializeField] private ReplayManager replayManager;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        closeAppButton.onClick.AddListener(() =>
        {
            Application.Quit();
        });

        restartButton.onClick.AddListener(() =>
        {
            replayManager.RestartReplay();
            gameObject.SetActive(false);
        });
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
