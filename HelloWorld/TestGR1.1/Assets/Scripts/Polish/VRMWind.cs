using UnityEngine;
using VRM;

public class VRMWind : MonoBehaviour
{

    [SerializeField] private VRMSpringBone[] springBones; // Kéo các component Spring Bone của tóc vào đây
    [Tooltip("Độ mạnh của gió, điều chỉnh để tóc lung lay nhiều hay ít")]
    [SerializeField, Range(0, 2)] private float windStrength = 0.5f;
    [Tooltip("Tốc độ thay đổi của gió, điều chỉnh để tóc lung lay nhanh hay chậm")]
    [SerializeField, Range(0, 5)] private float windSpeed = 2.0f;

    private Vector3 baseGravity = new Vector3(0, -9.81f, 0);

    void Update()
    {
        // Sử dụng hàm Sin/Cos kết hợp với Mathf.PerlinNoise để tạo độ nhấp nhô tự nhiên của gió
        float windEffectX = Mathf.PerlinNoise(Time.time * windSpeed, 0) * windStrength;
        float windEffectZ = Mathf.Sin(Time.time * windSpeed) * (windStrength * 0.5f);

        Vector3 newGravity = baseGravity + new Vector3(windEffectX, 0, windEffectZ);

        foreach (var bone in springBones)
        {
            // Thay đổi hướng lực tác động liên tục để ép tóc phải lung lay
            bone.m_gravityDir = newGravity.normalized;
        }
    }
}
