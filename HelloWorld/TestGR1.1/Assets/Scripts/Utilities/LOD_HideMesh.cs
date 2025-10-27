using System.Collections.Generic;
using UnityEngine;

public class LOD_HideMesh : MonoBehaviour
{
    [SerializeField] private List<MeshRenderer> meshRenderers;
    [SerializeField] private float hideDistance = 300f;
    void Start()
    {
        if (meshRenderers == null || meshRenderers.Count == 0)
        {
            meshRenderers = new List<MeshRenderer>(GetComponentsInChildren<MeshRenderer>());
        }
    }

    void Update()
    {
        if (Camera.main != null)
        {
            float distance = Vector3.Distance(Camera.main.transform.position, transform.position);
            bool shouldHide = distance > hideDistance;
            foreach (MeshRenderer mr in meshRenderers)
            {
                if (mr != null)
                {
                    mr.enabled = !shouldHide;
                }
            }
        }
    }
}
