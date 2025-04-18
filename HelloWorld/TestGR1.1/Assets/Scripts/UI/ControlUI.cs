using UnityEngine;

public class ControlUI : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        GameInput.Instance.OnToggleController += (sender, args) =>
		{
			gameObject.SetActive(!gameObject.activeSelf);
		};
	}
}
