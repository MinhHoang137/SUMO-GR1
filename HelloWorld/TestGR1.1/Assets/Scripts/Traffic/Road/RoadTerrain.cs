using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;

// "Nặn" Unity Terrain (heightmap) cho khít mạng lưới đường:
//   - Quét mọi lane (dải polyline có width) + junction (đa giác) → splat cao độ mặt đường vào lưới heightmap.
//   - Tại mỗi ô lưới, nếu nhiều lớp chồng nhau (cầu vượt / đường ngầm / nhiều lane) → giữ cao độ THẤP NHẤT
//     ("nặn theo cái thấp nhất"): terrain ôm đáy, các lớp trên nổi phía trên.
//   - Ô không có đường phủ → lấp theo ô đường GẦN NHẤT (BFS) để terrain liền mạch, hoặc phẳng tại đáy.
//   - Hạ thêm `heightEpsilon` để terrain nằm ngay dưới mặt đường, tránh z-fight.
//
// Khác Floor.cs (một Plane phẳng): script này biến dạng heightmap thật của Terrain đang gắn cùng GameObject.
[RequireComponent(typeof(Terrain), typeof(TerrainCollider))]
public class RoadTerrain : MonoBehaviour
{
    public enum OffRoadMode
    {
        HugNearest, // Lấp ô trống theo cao độ ô đường gần nhất (BFS) → terrain ôm sát mạng, không vách hụt.
        FlatBase    // Mọi ô off-road = cao độ thấp nhất toàn mạng.
    }

    [SerializeField] private RoadDataSO roadDataSO;

    [Header("Cao độ")]
    [Tooltip("Hạ heightmap xuống dưới mặt đường (mét) để tránh z-fight tại seam terrain ↔ mặt đường.")]
    [SerializeField, Min(0f)] private float heightEpsilon = 0.05f;
    [Tooltip("Đệm dọc (mét) thêm dưới điểm thấp nhất / trên điểm cao nhất khi auto-fit size.y của terrain. " +
             "Đủ để mọi cao độ đường rơi vào dải [0,1] heightmap.")]
    [SerializeField, Min(0f)] private float verticalPadding = 10f;

    [Header("Phạm vi (auto-fit)")]
    [Tooltip("Tự đặt vị trí + kích thước terrain phủ AABB mạng lưới. Tắt nếu muốn giữ nguyên size/pos đã cấu hình.")]
    [SerializeField] private bool autoFit = true;
    [Tooltip("Lề ngang (mét) nới rộng terrain quanh AABB mạng lưới khi auto-fit.")]
    [SerializeField, Min(0f)] private float horizontalMargin = 20f;

    [Header("Lấp vùng off-road")]
    [SerializeField] private OffRoadMode offRoadMode = OffRoadMode.HugNearest;

    [Header("An toàn asset")]
    [Tooltip("Clone TerrainData lúc runtime để KHÔNG ghi đè asset gốc trên đĩa (tránh bẩn git mỗi lần chạy).")]
    [SerializeField] private bool cloneTerrainData = true;

    [Header("Hiệu năng")]
    [Tooltip("Chạy phần tính heightmap (splat + BFS + chuẩn hoá) trên background thread để không freeze frame. " +
             "Setup khung terrain + SetHeights vẫn ở main thread. Tắt nếu cần xác định (single-thread).")]
    [SerializeField] private bool useBackgroundThread = true;

    private Terrain terrain;
    private TerrainCollider terrainCollider;

    void Start()
    {
        terrain = GetComponent<Terrain>();
        terrainCollider = GetComponent<TerrainCollider>();

        StartCoroutine(ManipulateAction.Wait(
            () => roadDataSO == null
                || ((roadDataSO.edgeDatas == null || roadDataSO.edgeDatas.Count == 0)
                    && (roadDataSO.junctionDatas == null || roadDataSO.junctionDatas.Count == 0)),
            () => StartCoroutine(SculptRoutine())));
    }

    private IEnumerator SculptRoutine()
    {
        // ===== Main thread: chuẩn bị TerrainData + khung (size/pos) =====
        TerrainData data = terrain.terrainData;
        if (data == null) yield break;

        if (cloneTerrainData)
        {
            data = Instantiate(data);
            terrain.terrainData = data;
            terrainCollider.terrainData = data;
        }

        if (!TryComputeBounds(out float minX, out float maxX, out float minZ, out float maxZ,
                              out float minY, out float maxY))
        {
            yield break;
        }

        // --- Đặt khung terrain (vị trí góc dưới-trái + size) ---
        Vector3 terrainPos;
        Vector3 size;
        if (autoFit)
        {
            terrainPos = new Vector3(minX - horizontalMargin, minY - verticalPadding, minZ - horizontalMargin);
            size = new Vector3(
                (maxX - minX) + 2f * horizontalMargin,
                (maxY - minY) + 2f * verticalPadding,
                (maxZ - minZ) + 2f * horizontalMargin);
            // size.y phải > 0 để chuẩn hoá heightmap; mạng phẳng tuyệt đối vẫn cần dải dương.
            if (size.y < 1f) size.y = Mathf.Max(1f, 2f * verticalPadding);
            data.size = size;
            transform.position = terrainPos;
        }
        else
        {
            terrainPos = transform.position;
            size = data.size;
        }

        int res = data.heightmapResolution;
        // Bề rộng thật / ô lưới (mét). Dùng làm bước sample để phủ kín không hở.
        float cellWorldX = size.x / (res - 1);
        float cellWorldZ = size.z / (res - 1);
        float sampleStep = 0.5f * Mathf.Min(cellWorldX, cellWorldZ);
        if (sampleStep < 1e-3f) sampleStep = 1e-3f;

        // ===== Phần nặng: tính heightmap chuẩn hoá. Toàn hàm thuần (mảng cục bộ + Vector3/Mathf),
        // an toàn chạy off-thread. roadDataSO chỉ ĐỌC, không sửa. =====
        float[,] heights;
        if (useBackgroundThread)
        {
            Task<float[,]> task = Task.Run(() => ComputeHeights(terrainPos, size, res, sampleStep, minY));
            while (!task.IsCompleted) yield return null;   // không freeze frame trong lúc tính
            if (task.IsFaulted)
            {
                Debug.LogException(task.Exception);
                yield break;
            }
            heights = task.Result;
        }
        else
        {
            heights = ComputeHeights(terrainPos, size, res, sampleStep, minY);
        }

        // ===== Main thread: áp heightmap =====
        data.SetHeights(0, 0, heights);
    }

    // Tính heightmap chuẩn hoá [0,1]. KHÔNG gọi Unity API main-thread (an toàn trên background thread).
    private float[,] ComputeHeights(Vector3 terrainPos, Vector3 size, int res, float sampleStep, float minY)
    {
        // Lưới cao độ THẾ GIỚI (mét), khởi tạo "chưa có dữ liệu".
        float[,] worldH = new float[res, res];
        bool[,] covered = new bool[res, res];
        for (int z = 0; z < res; z++)
            for (int x = 0; x < res; x++)
                worldH[z, x] = float.PositiveInfinity;

        // --- Splat lanes ---
        if (roadDataSO.edgeDatas != null)
        {
            foreach (EdgeData edge in roadDataSO.edgeDatas)
            {
                if (edge?.lanes == null) continue;
                foreach (Lane lane in edge.lanes)
                {
                    SplatLane(lane, worldH, covered, terrainPos, size, res, sampleStep);
                }
            }
        }

        // --- Splat junctions ---
        if (roadDataSO.junctionDatas != null)
        {
            foreach (JunctionData junction in roadDataSO.junctionDatas)
            {
                SplatJunction(junction, worldH, covered, terrainPos, size, res);
            }
        }

        // --- Lấp ô off-road ---
        FillUncovered(worldH, covered, res, minY);

        // --- Chuyển sang heightmap chuẩn hoá [0,1] ---
        float[,] heights = new float[res, res];
        float invSizeY = size.y > 1e-6f ? 1f / size.y : 0f;
        for (int z = 0; z < res; z++)
        {
            for (int x = 0; x < res; x++)
            {
                float h = worldH[z, x] - heightEpsilon;
                heights[z, x] = Mathf.Clamp01((h - terrainPos.y) * invSizeY);
            }
        }
        return heights;
    }

    // Splat một lane: đi dọc polyline, mỗi segment quét ngang theo width + dọc theo chiều dài,
    // cao độ Y nội suy tuyến tính dọc segment (đường phẳng ngang theo bề rộng). Giữ MIN tại mỗi ô.
    private void SplatLane(Lane lane, float[,] worldH, bool[,] covered,
                           Vector3 terrainPos, Vector3 size, int res, float sampleStep)
    {
        if (lane?.points == null || lane.points.Count < 2) return;
        float halfWidth = lane.width * 0.5f;

        for (int i = 0; i < lane.points.Count - 1; i++)
        {
            Vector3 a = Converter.ToVector3(lane.points[i]);
            Vector3 b = Converter.ToVector3(lane.points[i + 1]);
            Vector3 seg = b - a;
            float segLen = new Vector2(seg.x, seg.z).magnitude;
            if (segLen < 1e-4f) continue;

            Vector3 dir = seg / segLen;
            Vector3 right = Vector3.Cross(dir, -Vector3.up); // cùng convention Edge.cs
            int alongSteps = Mathf.Max(1, Mathf.CeilToInt(segLen / sampleStep));
            int acrossSteps = Mathf.Max(1, Mathf.CeilToInt((2f * halfWidth) / sampleStep));

            for (int s = 0; s <= alongSteps; s++)
            {
                float t = (float)s / alongSteps;
                Vector3 center = a + seg * t;
                float y = Mathf.Lerp(a.y, b.y, t); // cao độ dọc đường
                for (int w = 0; w <= acrossSteps; w++)
                {
                    float off = Mathf.Lerp(-halfWidth, halfWidth, (float)w / acrossSteps);
                    Vector3 p = center + right * off;
                    Splat(p.x, p.z, y, worldH, covered, terrainPos, size, res);
                }
            }
        }
    }

    // Splat một junction (đa giác): rasterize các ô trong bbox, point-in-polygon trên XZ,
    // cao độ nội suy IDW từ các đỉnh polygon. Giữ MIN.
    private void SplatJunction(JunctionData junction, float[,] worldH, bool[,] covered,
                               Vector3 terrainPos, Vector3 size, int res)
    {
        if (junction?.vertices == null || junction.vertices.Count < 3) return;

        int n = junction.vertices.Count;
        Vector3[] poly = new Vector3[n];
        float jMinX = float.MaxValue, jMaxX = float.MinValue, jMinZ = float.MaxValue, jMaxZ = float.MinValue;
        for (int i = 0; i < n; i++)
        {
            poly[i] = Converter.ToVector3(junction.vertices[i]);
            jMinX = Mathf.Min(jMinX, poly[i].x); jMaxX = Mathf.Max(jMaxX, poly[i].x);
            jMinZ = Mathf.Min(jMinZ, poly[i].z); jMaxZ = Mathf.Max(jMaxZ, poly[i].z);
        }

        // Khoảng index lưới phủ bbox junction.
        WorldToIndex(jMinX, jMinZ, terrainPos, size, res, out int x0, out int z0);
        WorldToIndex(jMaxX, jMaxZ, terrainPos, size, res, out int x1, out int z1);
        x0 = Mathf.Clamp(x0, 0, res - 1); x1 = Mathf.Clamp(x1, 0, res - 1);
        z0 = Mathf.Clamp(z0, 0, res - 1); z1 = Mathf.Clamp(z1, 0, res - 1);

        float cellWorldX = size.x / (res - 1);
        float cellWorldZ = size.z / (res - 1);
        for (int zi = z0; zi <= z1; zi++)
        {
            float wz = terrainPos.z + zi * cellWorldZ;
            for (int xi = x0; xi <= x1; xi++)
            {
                float wx = terrainPos.x + xi * cellWorldX;
                if (!PointInPolygonXZ(wx, wz, poly)) continue;
                float y = IdwHeight(wx, wz, poly);
                ApplyMin(worldH, covered, zi, xi, y);
            }
        }
    }

    private void Splat(float wx, float wz, float y, float[,] worldH, bool[,] covered,
                       Vector3 terrainPos, Vector3 size, int res)
    {
        WorldToIndex(wx, wz, terrainPos, size, res, out int xi, out int zi);
        if (xi < 0 || xi >= res || zi < 0 || zi >= res) return;
        ApplyMin(worldH, covered, zi, xi, y);
    }

    private static void ApplyMin(float[,] worldH, bool[,] covered, int zi, int xi, float y)
    {
        if (y < worldH[zi, xi]) worldH[zi, xi] = y;
        covered[zi, xi] = true;
    }

    private static void WorldToIndex(float wx, float wz, Vector3 terrainPos, Vector3 size, int res,
                                     out int xi, out int zi)
    {
        xi = Mathf.RoundToInt((wx - terrainPos.x) / size.x * (res - 1));
        zi = Mathf.RoundToInt((wz - terrainPos.z) / size.z * (res - 1));
    }

    // Lấp các ô chưa được đường phủ. HugNearest: BFS đa nguồn từ mọi ô covered → gán cao độ ô gần nhất.
    // FlatBase: đặt tất cả về minY.
    private void FillUncovered(float[,] worldH, bool[,] covered, int res, float minY)
    {
        if (offRoadMode == OffRoadMode.FlatBase)
        {
            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++)
                    if (!covered[z, x]) worldH[z, x] = minY;
            return;
        }

        // BFS đa nguồn (4-neighbor). Hàng đợi mã hoá index = z * res + x.
        Queue<int> queue = new Queue<int>();
        bool[,] filled = new bool[res, res];
        for (int z = 0; z < res; z++)
        {
            for (int x = 0; x < res; x++)
            {
                if (covered[z, x])
                {
                    filled[z, x] = true;
                    queue.Enqueue(z * res + x);
                }
            }
        }

        if (queue.Count == 0)
        {
            // Không có đường nào phủ → phẳng đáy.
            for (int z = 0; z < res; z++)
                for (int x = 0; x < res; x++)
                    worldH[z, x] = minY;
            return;
        }

        int[] dz = { 1, -1, 0, 0 };
        int[] dx = { 0, 0, 1, -1 };
        while (queue.Count > 0)
        {
            int cur = queue.Dequeue();
            int cz = cur / res;
            int cx = cur % res;
            for (int k = 0; k < 4; k++)
            {
                int nz = cz + dz[k];
                int nx = cx + dx[k];
                if (nz < 0 || nz >= res || nx < 0 || nx >= res) continue;
                if (filled[nz, nx]) continue;
                filled[nz, nx] = true;
                worldH[nz, nx] = worldH[cz, cx]; // kế thừa cao độ ô nguồn gần nhất
                queue.Enqueue(nz * res + nx);
            }
        }
    }

    // Quét mọi điểm hình học để lấy AABB ngang (XZ) + dải cao độ (Y). Tọa độ thế giới (qua Converter).
    private bool TryComputeBounds(out float minX, out float maxX, out float minZ, out float maxZ,
                                  out float minY, out float maxY)
    {
        minX = minZ = minY = float.MaxValue;
        maxX = maxZ = maxY = float.MinValue;
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
                        Accumulate(Converter.ToVector3(point), ref minX, ref maxX, ref minZ, ref maxZ, ref minY, ref maxY);
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
                    Accumulate(Converter.ToVector3(vertex), ref minX, ref maxX, ref minZ, ref maxZ, ref minY, ref maxY);
                    any = true;
                }
            }
        }

        return any;
    }

    private static void Accumulate(Vector3 p, ref float minX, ref float maxX, ref float minZ, ref float maxZ,
                                   ref float minY, ref float maxY)
    {
        if (p.x < minX) minX = p.x;
        if (p.x > maxX) maxX = p.x;
        if (p.z < minZ) minZ = p.z;
        if (p.z > maxZ) maxZ = p.z;
        if (p.y < minY) minY = p.y;
        if (p.y > maxY) maxY = p.y;
    }

    // Point-in-polygon (ray casting) trên mặt phẳng XZ.
    private static bool PointInPolygonXZ(float px, float pz, Vector3[] poly)
    {
        bool inside = false;
        int n = poly.Length;
        for (int i = 0, j = n - 1; i < n; j = i++)
        {
            float zi = poly[i].z, zj = poly[j].z;
            float xi = poly[i].x, xj = poly[j].x;
            bool intersect = ((zi > pz) != (zj > pz))
                && (px < (xj - xi) * (pz - zi) / (zj - zi + 1e-12f) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    }

    // Nội suy cao độ trong polygon bằng inverse-distance weighting trên các đỉnh.
    private static float IdwHeight(float px, float pz, Vector3[] poly)
    {
        float sumW = 0f, sumWH = 0f;
        for (int i = 0; i < poly.Length; i++)
        {
            float ddx = px - poly[i].x;
            float ddz = pz - poly[i].z;
            float d2 = ddx * ddx + ddz * ddz;
            if (d2 < 1e-6f) return poly[i].y;
            float w = 1f / d2;
            sumW += w;
            sumWH += w * poly[i].y;
        }
        return sumW > 0f ? sumWH / sumW : poly[0].y;
    }
}
