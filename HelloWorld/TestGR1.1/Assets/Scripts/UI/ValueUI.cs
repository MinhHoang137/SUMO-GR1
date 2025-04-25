using System;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

[Serializable]
public class ValueUI
{
    [SerializeField] private string key;
    [SerializeField] private Slider slider;
    [SerializeField] private TMP_InputField inputField;
    [SerializeField] private Action<float> setter;
	public void Create(Action<float> setter)
	{
		this.setter = setter;
		if (PlayerPrefs.HasKey(key))
		{
			slider.value = PlayerPrefs.GetFloat(key);
		}
		this.setter?.Invoke(slider.value);
		inputField.text = slider.value.ToString("0.00");
		slider.onValueChanged.AddListener((value) =>
		{
			inputField.text = value.ToString("0.00");
			this.setter?.Invoke(value);
		});
		inputField.onEndEdit.AddListener((value) =>
		{
			if (float.TryParse(value, out float result))
			{
				slider.value = result;
				this.setter?.Invoke(result);
			}
			else
			{
				inputField.text = slider.value.ToString("0.00");
			}
		});
	}
	public void Destroy()
	{
		slider.onValueChanged.RemoveAllListeners();
		inputField.onEndEdit.RemoveAllListeners();
		PlayerPrefs.SetFloat(key, slider.value);
		PlayerPrefs.Save();
	}
}
