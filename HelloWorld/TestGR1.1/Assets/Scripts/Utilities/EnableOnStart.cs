using Unity.VisualScripting;
using UnityEngine;

public class EnableOnStart : MonoBehaviour
{
    [SerializeField] private bool enableOnStart = false;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        gameObject.SetActive(enableOnStart);
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
