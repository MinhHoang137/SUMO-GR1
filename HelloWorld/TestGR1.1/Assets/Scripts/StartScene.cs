using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class StartScene : MonoBehaviour
{
    [SerializeField] private Button startButton;
	[SerializeField] private RoadDataListener roadDataListener;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		startButton.onClick.AddListener(() =>
		{
			if (!roadDataListener.IsListening())
			{
				SceneManager.LoadScene(1);
			}
				
		});
	}
}
