using UnityEngine;

public class OptionUI : MonoBehaviour
{
	private bool previousMouseEnabled = false;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
	{
		GameInput.Instance.OnToggleOptions += (sender, args) =>
		{
			gameObject.SetActive(!gameObject.activeSelf);
			if (gameObject.activeSelf)
			{
				previousMouseEnabled = GameInput.Instance.MouseEnabled;
				GameInput.Instance.SetMouse(true);
			}
			else
			{
				GameInput.Instance.SetMouse(previousMouseEnabled);
			};
			
		};
		gameObject.SetActive(false);
	}
} 
