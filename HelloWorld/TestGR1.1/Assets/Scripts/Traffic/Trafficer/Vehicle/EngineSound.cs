using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class EngineSound : MonoBehaviour
{
    private AudioSource audioSource;
    private AudioClip currentClip;
    [SerializeField] private EngineSoundSO engineSoundSO;
    [SerializeField] private float slowSpeedThreshold = 0.1f;
    [Range(0f, 100f)]
    // [SerializeField] private float accelerationThreshold = 0.5f;

    private Vector3 previousPosition;
    private float previousSpeed = 0f;
    private float currentSpeed = 0f;
    private float smoothedSpeed = 0f;
    private float smoothedAcceleration = 0f;
    
    [Header("Smoothing")]
    [SerializeField] private float speedSmoothTime = 5f;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        previousPosition = transform.position;
    }

    // Update is called once per frame
    void Update()
    {
        UpdateEngineSound();
    }

    private float CalculateAcceleration()
    {
        if (Time.deltaTime <= 0) return 0f;

        // Vận tốc và tốc độ tức thời ở frame này
        Vector3 currentVelocity = (transform.position - previousPosition) / Time.deltaTime;
        float rawSpeed = currentVelocity.magnitude; // Dùng magnitude ổn định hơn Dot khi xoay xe
        
        // Làm mượt tốc độ (tránh biến thiên do Time.deltaTime giật)
        smoothedSpeed = Mathf.Lerp(smoothedSpeed, rawSpeed, Time.deltaTime * speedSmoothTime);
        currentSpeed = smoothedSpeed; // Nếu bạn muốn lấy từ ngoài

        // Tính gia tốc dựa trên tốc độ đã làm mượt
        float rawAcceleration = (smoothedSpeed - previousSpeed) / Time.deltaTime;
        
        // Tiếp tục làm mượt gia tốc để chắc chắn không bị nhiễu cục bộ
        smoothedAcceleration = Mathf.Lerp(smoothedAcceleration, rawAcceleration, Time.deltaTime * speedSmoothTime);

        // Cập nhật lưu trữ cho frame sau
        previousPosition = transform.position;
        previousSpeed = smoothedSpeed;
        
        return smoothedAcceleration;
    }

    private void UpdateEngineSound()
    {
        float acceleration = CalculateAcceleration();
        AudioClip newClip;

        // Kiểm tra dựa trên giá trị đã được làm mượt
        if (smoothedSpeed < slowSpeedThreshold)
        {
            newClip = engineSoundSO.IdleSound;
        }
        else {
            newClip = engineSoundSO.StableSound;
        }

        if (newClip != currentClip)
        { 
            if (!audioSource.enabled){
                return;
            }
            audioSource.clip = newClip;
            audioSource.loop = true;
            audioSource.Play();
            currentClip = newClip;
        }
    }
}
