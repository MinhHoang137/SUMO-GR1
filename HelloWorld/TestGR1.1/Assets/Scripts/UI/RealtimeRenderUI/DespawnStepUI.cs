using UnityEngine;

public class DespawnStepUI : MonoBehaviour
{
    [SerializeField] private ValueUI despawnStepValueUI;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        despawnStepValueUI.Create((value) =>
        {
            TrafficerManager.Instance.WreckLifetimeSteps = Mathf.RoundToInt(value);
        });
    }

    // Update is called once per frame
    void Update()
    {
        
    }
    private void OnDestroy()
    {
        despawnStepValueUI.Destroy();
    }
}
