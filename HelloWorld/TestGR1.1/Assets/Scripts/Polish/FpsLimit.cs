using UnityEngine;

public class FpsLimit : MonoBehaviour
{
    [SerializeField, Range(60, 500)] private int targetFps = 60;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        Application.targetFrameRate = targetFps;
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
