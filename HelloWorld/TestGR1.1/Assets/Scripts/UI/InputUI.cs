using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class InputUI : MonoBehaviour
{
	[SerializeField] private TMP_Text moveUpText;
	[SerializeField] private Button moveUpButton;

	[SerializeField] private TMP_Text moveDownText;
	[SerializeField] private Button moveDownButton;

	[SerializeField] private TMP_Text moveLeftText;
	[SerializeField] private Button moveLeftButton;

	[SerializeField] private TMP_Text moveRightText;
	[SerializeField] private Button moveRightButton;

	[SerializeField] private TMP_Text freeToggleText;
	[SerializeField] private Button freeToggleButton;

	[SerializeField] private TMP_Text mouseToggleText;
	[SerializeField] private Button mouseToggleButton;

	[SerializeField] private TMP_Text toggleControllerText;
	[SerializeField] private Button toggleControllerButton;

	[SerializeField] private TMP_Text toggleOptionsText;
	[SerializeField] private Button toggleOptionsButton;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        SetInputUiText(moveUpText, moveUpButton, Binding.MoveUp);
		SetInputUiText(moveDownText, moveDownButton, Binding.MoveDown);
		SetInputUiText(moveLeftText, moveLeftButton, Binding.MoveLeft);
		SetInputUiText(moveRightText, moveRightButton, Binding.MoveRight);
		SetInputUiText(freeToggleText, freeToggleButton, Binding.FreeToggle);
		SetInputUiText(mouseToggleText, mouseToggleButton, Binding.MouseToggle);
		SetInputUiText(toggleControllerText, toggleControllerButton, Binding.ToggleController);
		SetInputUiText(toggleOptionsText, toggleOptionsButton, Binding.ToggleOptions);
	}

	private void SetInputUiText(TMP_Text inputText, Button button, Binding binding)
	{
		inputText.text = GameInput.Instance.GetBindingText(binding);
		RectTransform rect = button.GetComponent<RectTransform>();
		rect.sizeDelta = new Vector2(50 + 25 * (inputText.text.Length - 1), rect.sizeDelta.y);
	} 
}
