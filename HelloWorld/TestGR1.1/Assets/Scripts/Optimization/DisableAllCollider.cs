using UnityEngine;

public class DisableAllCollider : MonoBehaviour
{
    [SerializeField] private float delay = 0.5f; // Delay in seconds before disabling colliders
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        Collider[] colliders = GetComponentsInChildren<Collider>();
        StartCoroutine(ManipulateAction.Delay(() =>
        {
            foreach (Collider col in colliders)
            {
                if (col != null)
                {
                    col.enabled = false;
                }
            }
        }, delay));
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
