using UnityEngine;

[CreateAssetMenu(fileName = "MusicSO", menuName = "Scriptable Objects/MusicSO")]
public class MusicSO : ScriptableObject
{
    [SerializeField] private MusicData[] musicData;
    public MusicData GetMusicData(int index)
    {
        return musicData[index];
    }
    public int GetMusicDataCount()
    {
        return musicData.Length;
    }
}
[System.Serializable]
public struct MusicData
{
    public string name;
    public AudioClip clip;
}
