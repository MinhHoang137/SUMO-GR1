using UnityEngine;

public class EscHider : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        GameInput.Instance.OnToggleOptions += (sender, args) =>
        {
            gameObject.SetActive(false);
        };
    }
}
