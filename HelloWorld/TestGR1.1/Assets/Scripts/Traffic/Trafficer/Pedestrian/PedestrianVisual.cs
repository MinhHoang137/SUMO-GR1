using UnityEngine;

[RequireComponent(typeof(Animator))]
public class PedestrianVisual : MonoBehaviour
{
    private const string ANIMATOR_PARAM_SPEED = "Speed";
    private const string ANIMATOR_PARAM_MULTIPLIER = "Multiplier";
    [SerializeField] private Pedestrian pedestrian;

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
        animator.SetFloat(ANIMATOR_PARAM_SPEED, pedestrian.GetFullSpeed());
        animator.SetFloat(ANIMATOR_PARAM_MULTIPLIER, pedestrian.GetFullSpeed() / baseSpeed);
    }
}
