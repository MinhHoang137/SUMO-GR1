using System;
using Unity.VisualScripting;
using UnityEngine;
using UnityEngine.XR;

public class TrafficerSoundController : MonoBehaviour
{
    [SerializeField] private CameraController cameraController;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        cameraController.OnSetTrafficer += HandleSetTrafficer;
    }

    private void HandleSetTrafficer(object sender, CameraController.OnSetTrafficerEventArgs e)
    {
        if (e.newTrafficer != null)
        {
            MusicController musicController = e.newTrafficer.GetComponentInChildren<MusicController>();
            if (musicController != null)
            {
                musicController.Enable();
            }
            AudioSource[] audioSources = e.newTrafficer.GetComponentsInChildren<AudioSource>();
            foreach (AudioSource audioSource in audioSources)            {
                audioSource.enabled = true;
            }
        }
        if (e.preTrafficer != null)
        {
            MusicController musicController = e.preTrafficer.GetComponentInChildren<MusicController>();
            if (musicController != null)
            {
                musicController.Disable();
            }
            AudioSource[] audioSources = e.preTrafficer.GetComponentsInChildren<AudioSource>();
            foreach (AudioSource audioSource in audioSources)            {
                audioSource.enabled = false;
            }
        }
    }
}
