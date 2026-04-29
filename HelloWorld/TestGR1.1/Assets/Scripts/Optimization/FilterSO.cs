using UnityEngine;

// [CreateAssetMenu(fileName = "FilterSO", menuName = "Scriptable Objects/FilterSO")]
public class FilterSO : ScriptableObject
{
    [SerializeField] private bool useFilter = false;
    [SerializeField, Min(0)] private float filterDistance = 1000f;
    public float FilterDistance { get { return filterDistance; } }
    public bool GetUseFilter() { return useFilter; }
    public void SetUseFilter(bool useFilter)
    {
        this.useFilter = useFilter;
    }
}
