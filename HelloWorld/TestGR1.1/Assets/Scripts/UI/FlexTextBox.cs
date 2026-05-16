using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(TMP_InputField))]
public class FlexTextBox : MonoBehaviour
{
    private TMP_InputField inputField;
    private Vector2 originalTextSize;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        inputField = GetComponent<TMP_InputField>();
        // store original text component size so we can restore it when input is empty
        if (inputField.textComponent != null)
        {
            originalTextSize = inputField.textComponent.rectTransform.sizeDelta;
        }

        inputField.onValueChanged.AddListener(OnInputFieldValueChanged);

        // Adjust initially
        OnInputFieldValueChanged(inputField.text);
    }

    private void OnInputFieldValueChanged(string newValue)
    {
        if (inputField.textComponent == null) return;
        
        // Stop any previous resize routines to avoid overlapping operations
        StopAllCoroutines();
        StartCoroutine(ResizeRoutine(newValue));
    }

    private IEnumerator ResizeRoutine(string newValue)
    {
        // Wait until the end of the frame (so graphic rebuild loop completes)
        yield return new WaitForEndOfFrame();

        if (inputField == null || inputField.textComponent == null) yield break;

        RectTransform textRect = inputField.textComponent.rectTransform;

        if (string.IsNullOrWhiteSpace(newValue))
        {
            // keep original size when the value is empty or only whitespace
            textRect.sizeDelta = originalTextSize;
            yield break;
        }

        float newWidth = inputField.textComponent.GetPreferredValues(newValue).x;
        textRect.sizeDelta = new Vector2(newWidth, textRect.sizeDelta.y);

        // If you also want to resize the InputField itself, uncomment the following lines:
        // RectTransform inputRect = GetComponent<RectTransform>();
        // inputRect.sizeDelta = new Vector2(newWidth + padding, inputRect.sizeDelta.y);
    }

    private void OnDestroy()
    {
        if (inputField != null)
        {
            inputField.onValueChanged.RemoveListener(OnInputFieldValueChanged);
        }
    }
}
