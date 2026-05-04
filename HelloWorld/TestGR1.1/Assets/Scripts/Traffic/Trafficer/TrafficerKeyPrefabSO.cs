using System;
using UnityEngine;

// [CreateAssetMenu(fileName = "TrafficerKeyPrefabSO", menuName = "Scriptable Objects/TrafficerKeyPrefabSO")]
public class TrafficerKeyPrefabSO : ScriptableObject
{
    [SerializeField] private TrafficerKeyPrefab[] trafficerKeyPrefabs;

    public Trafficer GetRandomTrafficer(string type)
    {
        foreach (var keyPrefab in trafficerKeyPrefabs)
        {
            if (keyPrefab.Type == type)
            {
                var trafficers = keyPrefab.Trafficers;
                if (trafficers.Length > 0)
                {
                    int randomIndex = UnityEngine.Random.Range(0, trafficers.Length);
                    return trafficers[randomIndex];
                }
            }
        }
        Debug.LogWarning($"No trafficer found for type: {type}");
        return null;
    }
}

[Serializable]
public struct TrafficerKeyPrefab
{
    [SerializeField] private string type;
    [SerializeField] private Trafficer[] trafficers;
    public readonly string Type => type;
    public readonly Trafficer[] Trafficers => trafficers;
}