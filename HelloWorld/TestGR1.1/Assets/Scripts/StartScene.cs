using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class StartScene : MonoBehaviour
{
    [SerializeField] private Button startButton;
	[SerializeField] private JunctionReader junctionReader;
    [SerializeField] private EdgeReader edgeReader;
	[SerializeField] private CrossingReader crossingReader;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		startButton.onClick.AddListener(() =>
		{
			if (!junctionReader.IsListening() && !edgeReader.IsListening() && !crossingReader.IsListening())
			{
				SceneManager.LoadScene(1);
			}
		});
	}
}
