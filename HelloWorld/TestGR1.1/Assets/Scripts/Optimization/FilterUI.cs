using UnityEngine;
using UnityEngine.UI;

public class FilterUI : MonoBehaviour
{
    [SerializeField] private FilterSO filterSO;
    [SerializeField] private Toggle filterToggle;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        filterToggle.onValueChanged.AddListener((isOn) => filterSO.SetUseFilter(isOn));
    }

    
}
