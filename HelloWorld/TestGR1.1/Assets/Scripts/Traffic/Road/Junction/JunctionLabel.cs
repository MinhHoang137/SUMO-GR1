using TMPro;
using UnityEngine;

public class JunctionLabel : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI label;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        float x = Camera.main.transform.forward.x;
        float z = Camera.main.transform.forward.z;
        transform.forward = new Vector3(x, 0, z);
    }

    public void SetText(string text)
    {
        label.text = text;
    }
}
