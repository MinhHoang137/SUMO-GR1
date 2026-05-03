using UnityEngine;

[CreateAssetMenu(fileName = "EngineSoundSO", menuName = "Scriptable Objects/EngineSoundSO")]
public class EngineSoundSO : ScriptableObject
{
    [SerializeField] private AudioClip idleSound;
    [SerializeField] private AudioClip accelerationSound;
    [SerializeField] private AudioClip stableSound;
    public AudioClip IdleSound => idleSound;
    public AudioClip AccelerationSound => accelerationSound;
    public AudioClip StableSound => stableSound;
}
