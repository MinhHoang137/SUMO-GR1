using UnityEngine;

[RequireComponent(typeof(Animator))]
public class PedestrianVisual : MonoBehaviour
{
    private const string ANIMATOR_PARAM_SPEED = "Speed";
    private const string ANIMATOR_PARAM_MULTIPLIER = "Multiplier";
    [SerializeField] private Pedestrian pedestrian;
    [SerializeField] private PauseSO pauseSO;

    [SerializeField, Min(0.01f)] private float baseSpeed = 5f;
    private Animator animator;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        animator = GetComponent<Animator>();
    }

    // Update is called once per frame
    void LateUpdate()
    {
        // Pause → speed 0 để Animator đứng yên, tránh "đi tại chỗ" (speed lưu sẵn ≠ 0 dù vị trí đứng im).
        float speed = (pauseSO != null && pauseSO.isPaused) ? 0f : pedestrian.GetFullSpeed();
        animator.SetFloat(ANIMATOR_PARAM_SPEED, speed);
        animator.SetFloat(ANIMATOR_PARAM_MULTIPLIER, speed / baseSpeed);
    }
}
