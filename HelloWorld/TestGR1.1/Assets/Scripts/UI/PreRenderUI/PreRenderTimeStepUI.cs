using UnityEngine;

public class PreRenderTimeStepUI : MonoBehaviour
{
    [SerializeField] private ValueUI timeStepValueUI;
    [SerializeField] private SpeedMultiplierUI speedMultiplierUI;
    [SerializeField] private ReplayManager replayManager;
    private int currentTimeStep = 1000; // in milliseconds
    private bool isEditable = false;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        timeStepValueUI.Create((value) =>
        {
            // Ensure time step is at least 1 to avoid invalid configurations
            if (value < 1f)
            {
                value = 1f;
            }

            if (isEditable)
            {
                float ratio = value / currentTimeStep;
                speedMultiplierUI.ScaleValueInversely(ratio);
                currentTimeStep = (int)value;
                replayManager.SetTimeStep(currentTimeStep / 1000f); // Convert ms to seconds
            }
        });
        isEditable = true;
        currentTimeStep = (int)timeStepValueUI.GetValue();
        replayManager.SetTimeStep(currentTimeStep / 1000f); // Convert ms to seconds
    }

    

    
    private void OnDestroy()
    {
        timeStepValueUI.Destroy();
    }
}
