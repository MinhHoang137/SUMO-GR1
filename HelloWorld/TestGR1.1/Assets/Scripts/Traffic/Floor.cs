using UnityEngine;

// Đặt một mặt sàn (Unity Plane 10x10) phủ toàn mạng lưới đường:
//   - Vị trí = tâm bounding box (mặt XZ) của toàn bộ junction + edge.
//   - Cao độ Y = floorHeight (mặc định -0.005) để nằm ngay dưới mặt đường, tránh z-fight.
//   - Scale = gấp rưỡi (sizeMultiplier) kích thước bounding box.
//   - Hướng xoay = trùng bounding box (AABB trên XZ → không xoay).
public class Floor : MonoBehaviour
{
    private const float PlaneBaseSize = 10f; // Unity Plane mặc định 10x10 unit ở scale 1.

    [SerializeField] private RoadDataSO roadDataSO;
    [Tooltip("Cao độ Y của sàn (mét). Đặt âm nhỏ để nằm ngay dưới mặt đường, tránh z-fight.")]
    [SerializeField] private float floorHeight = -0.005f;
    [Tooltip("Hệ số nhân kích thước so với bounding box mạng lưới.")]
    [SerializeField] private float sizeMultiplier = 1.5f;

    void Start()
    {
        StartCoroutine(ManipulateAction.Wait(() =>
        {
            return roadDataSO == null
                || ((roadDataSO.edgeDatas == null || roadDataSO.edgeDatas.Count == 0)
                    && (roadDataSO.junctionDatas == null || roadDataSO.junctionDatas.Count == 0));
        }, FitToNetwork));
    }

    private void FitToNetwork()
    {
        if (!TryComputeBounds(out float minX, out float maxX, out float minZ, out float maxZ))
        {
            return;
        }

        float centerX = (minX + maxX) * 0.5f;
        float centerZ = (minZ + maxZ) * 0.5f;
        float sizeX = (maxX - minX) * sizeMultiplier;
        float sizeZ = (maxZ - minZ) * sizeMultiplier;

        transform.SetPositionAndRotation(
            new Vector3(centerX, floorHeight, centerZ),
            Quaternion.identity);
        transform.localScale = new Vector3(sizeX / PlaneBaseSize, 1f, sizeZ / PlaneBaseSize);
    }

    // Quét mọi điểm hình học (edge lane points + junction vertices) để lấy AABB trên XZ.
    private bool TryComputeBounds(out float minX, out float maxX, out float minZ, out float maxZ)
    {
        minX = minZ = float.MaxValue;
        maxX = maxZ = float.MinValue;
        bool any = false;

        if (roadDataSO.edgeDatas != null)
        {
            foreach (EdgeData edge in roadDataSO.edgeDatas)
            {
                if (edge?.lanes == null) continue;
                foreach (Lane lane in edge.lanes)
                {
                    if (lane?.points == null) continue;
                    foreach (Coordinate point in lane.points)
                    {
                        Vector3 p = Converter.ToVector3(point);
                        Accumulate(p, ref minX, ref maxX, ref minZ, ref maxZ);
                        any = true;
                    }
                }
            }
        }

        if (roadDataSO.junctionDatas != null)
        {
            foreach (JunctionData junction in roadDataSO.junctionDatas)
            {
                if (junction?.vertices == null) continue;
                foreach (JunctionData.Vertex vertex in junction.vertices)
                {
                    Vector3 p = Converter.ToVector3(vertex);
                    Accumulate(p, ref minX, ref maxX, ref minZ, ref maxZ);
                    any = true;
                }
            }
        }

        return any;
    }

    private static void Accumulate(Vector3 p, ref float minX, ref float maxX, ref float minZ, ref float maxZ)
    {
        if (p.x < minX) minX = p.x;
        if (p.x > maxX) maxX = p.x;
        if (p.z < minZ) minZ = p.z;
        if (p.z > maxZ) maxZ = p.z;
    }
}
