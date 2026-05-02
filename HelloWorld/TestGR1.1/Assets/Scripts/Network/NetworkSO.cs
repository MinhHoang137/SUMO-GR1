using UnityEngine;

// [CreateAssetMenu(fileName = "NetworkSO", menuName = "Scriptable Objects/NetworkSO")]
public class NetworkSO : ScriptableObject
{
    [SerializeField] private string host = Constant.LOOPBACK_ADDRESS;
    public string Host
    {
        get => host;
        set => host = value;
    }
}
