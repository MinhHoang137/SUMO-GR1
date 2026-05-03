using System.Collections;
using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class MusicController : MonoBehaviour
{
    [SerializeField] private MusicSO musicSO;
    private AudioSource audioSource;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        StartCoroutine(PlayMusicCoroutineLoop());
        Disable();
    }

    // Update is called once per frame
    void Update()
    {
        
    }
    private IEnumerator PlayMusicCoroutineLoop()
    {
        while (true)
        {
            int index = Random.Range(0, musicSO.GetMusicDataCount());
            MusicData musicData = musicSO.GetMusicData(index);
            audioSource.clip = musicData.clip;
            audioSource.Play();
            yield return new WaitForSeconds(musicData.clip.length);
        }
    }
    public void Enable()
    {
        this.enabled = true;
        audioSource.enabled = true;
    }
    public void Disable()
    {
        this.enabled = false;
        audioSource.enabled = false;
    }
}
