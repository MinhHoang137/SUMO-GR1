using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>
/// Gom Edge/Junction/Crossing share material trong từng ô grid XZ thành 1 mesh duy nhất
/// → giảm draw call mạnh trên map đô thị dày đặc.
///
/// Lý do KHÔNG dựa vào Script Execution Order: cả 3 Maker (Edge/Junction/Crossing) đều dùng
/// `StartCoroutine(ManipulateAction.Wait(...))` chờ data từ network tới mới spawn — không tạo
/// trong Start(). Vì vậy phải poll: chờ roadDataSO populated + childCount của các root ổn định
/// (không thay đổi qua N frame liên tiếp) rồi mới combine.
/// </summary>
public class DrawCallsReducer : MonoBehaviour
{
	[Header("Source containers (parent của các Edge/Junction/Crossing đã spawn)")]
	[SerializeField] private Transform edgeMakerRoot;
	[SerializeField] private Transform junctionMakerRoot;
	[SerializeField] private Transform crossingMakerRoot;
	[SerializeField] private RoadDataSO roadData;

	[Header("Output")]
	[Tooltip("Prefab dùng cho mỗi combined mesh cell. Phải có MeshFilter + MeshRenderer. " +
	         "Đính kèm FilterTransform (hoặc component khác) nếu muốn — chúng sẽ tự được gắn " +
	         "lên từng cell. Mesh & material sẽ được Reducer set runtime.")]
	[SerializeField] private GameObject combinedCellPrefab;

	[Header("Batching")]
	[Tooltip("Kích thước ô grid XZ (m). 100m hợp với đô thị dày đặc; tăng 200–500 cho ngoại ô/highway. " +
	         "Ô nhỏ → nhiều cell (tốt cho frustum culling) nhưng draw call gain ít hơn. " +
	         "Ô lớn → ít draw call hơn nhưng combined mesh to (kém culling, dễ chạm giới hạn vertex).")]
	[SerializeField, Min(10f)] private float cellSize = 100f;

	[Tooltip("Số frame liên tiếp childCount phải ổn định trước khi combine. Tránh race condition " +
	         "khi maker còn đang trong vòng lặp spawn.")]
	[SerializeField, Min(1)] private int stableFrames = 3;

	[Tooltip("Sau khi combine, vô hiệu hoá Renderer của object gốc (giữ GameObject để script/UI còn " +
	         "truy cập được). Tắt nếu muốn so sánh trước/sau.")]
	[SerializeField] private bool disableOriginalRenderers = true;

	[Header("Debug")]
	[SerializeField] private bool logSummary = true;

	private Transform combinedRoot;

	private IEnumerator Start()
	{
		// Chờ roadData populated (network arrival).
		while (roadData == null
		       || roadData.edgeDatas == null
		       || roadData.junctionDatas == null
		       || roadData.crossingDatas == null)
		{
			yield return null;
		}

		// Chờ các Maker spawn xong (childCount ổn định N frame liên tiếp).
		yield return WaitUntilSpawningStable();

		Combine();
	}

	private IEnumerator WaitUntilSpawningStable()
	{
		int prevE = -1, prevJ = -1, prevC = -1;
		int stable = 0;
		while (stable < stableFrames)
		{
			int e = edgeMakerRoot != null ? edgeMakerRoot.childCount : 0;
			int j = junctionMakerRoot != null ? junctionMakerRoot.childCount : 0;
			int c = crossingMakerRoot != null ? crossingMakerRoot.childCount : 0;
			if (e == prevE && j == prevJ && c == prevC && (e + j + c) > 0)
				stable++;
			else
				stable = 0;
			prevE = e; prevJ = j; prevC = c;
			yield return null;
		}
	}

	private void Combine()
	{
		combinedRoot = new GameObject("_CombinedRoadMeshes").transform;
		combinedRoot.SetParent(transform, worldPositionStays: false);

		// Key: (material, cellX, cellZ). Value: list CombineInstance đã tính sẵn matrix tới world.
		var buckets = new Dictionary<BucketKey, List<CombineInstance>>();

		int gatheredCount = 0;
		gatheredCount += Gather(edgeMakerRoot, buckets);
		gatheredCount += Gather(junctionMakerRoot, buckets);
		gatheredCount += Gather(crossingMakerRoot, buckets);

		int emittedDrawCalls = 0;
		foreach (var kv in buckets)
		{
			List<CombineInstance> instances = kv.Value;
			if (instances.Count == 0) continue;

			// Đặt GO combined tại tâm cell → mesh vertex được dịch về local space của cell.
			// Tránh fp precision khi map xa gốc toạ độ (vài km).
			Vector3 cellCenter = new Vector3(
				(kv.Key.CellX + 0.5f) * cellSize,
				0f,
				(kv.Key.CellZ + 0.5f) * cellSize);

			Matrix4x4 worldToCell = Matrix4x4.Translate(-cellCenter);
			for (int i = 0; i < instances.Count; i++)
			{
				CombineInstance ci = instances[i];
				ci.transform = worldToCell * ci.transform;
				instances[i] = ci;
			}

			Mesh combined = new Mesh();
			combined.indexFormat = IndexFormat.UInt32; // > 65535 verts safe
			combined.CombineMeshes(instances.ToArray(), mergeSubMeshes: true, useMatrices: true);
			combined.RecalculateBounds();

			// Instantiate prefab (chứa MeshFilter + MeshRenderer + FilterTransform/component khác
			// user đã wire sẵn) thay vì new GameObject — để DrawCallsReducer không cần biết
			// tới các component optimization (FilterTransform, FilterSO, ...).
			GameObject go = Instantiate(combinedCellPrefab, combinedRoot);
			go.name = $"Cell_{kv.Key.CellX}_{kv.Key.CellZ}_{kv.Key.Material.name}";
			go.transform.SetPositionAndRotation(cellCenter, Quaternion.identity);
			go.transform.localScale = Vector3.one;

			// MF/MR cho phép tồn tại sẵn ở root hoặc child (linh hoạt cấu trúc prefab); nếu cả
			// hai đều thiếu, tự AddComponent vào root để user không phải nhớ gắn.
			MeshFilter mf = go.GetComponentInChildren<MeshFilter>(includeInactive: true);
			if (mf == null) mf = go.AddComponent<MeshFilter>();
			if (!mf.TryGetComponent(out MeshRenderer mr)) mr = mf.gameObject.AddComponent<MeshRenderer>();
			mf.sharedMesh = combined;
			mr.sharedMaterial = kv.Key.Material;
			emittedDrawCalls++;
		}

		if (disableOriginalRenderers)
		{
			DisableRenderersUnder(edgeMakerRoot);
			DisableRenderersUnder(junctionMakerRoot);
			DisableRenderersUnder(crossingMakerRoot);
		}

		if (logSummary)
		{
			Debug.Log($"[DrawCallsReducer] Combined {gatheredCount} renderers → {emittedDrawCalls} draw calls" +
			          $" ({(gatheredCount > 0 ? 100f * (1f - (float)emittedDrawCalls / gatheredCount) : 0f):F1}% reduction)" +
			          $", cellSize={cellSize}m");
		}
	}

	private int Gather(Transform root, Dictionary<BucketKey, List<CombineInstance>> buckets)
	{
		if (root == null) return 0;
		int count = 0;
		MeshFilter[] mfs = root.GetComponentsInChildren<MeshFilter>(includeInactive: false);
		foreach (MeshFilter mf in mfs)
		{
			if (mf.sharedMesh == null) continue;
			MeshRenderer mr = mf.GetComponent<MeshRenderer>();
			if (mr == null || !mr.enabled) continue;
			Material[] mats = mr.sharedMaterials;
			if (mats == null || mats.Length == 0 || mats[0] == null) continue;

			// Chỉ batch theo material đầu (submesh 0). Multi-submesh hiếm gặp với Edge/Junction.
			Material mat = mats[0];

			Vector3 worldPos = mf.transform.position;
			int cx = Mathf.FloorToInt(worldPos.x / cellSize);
			int cz = Mathf.FloorToInt(worldPos.z / cellSize);
			BucketKey key = new BucketKey(mat, cx, cz);

			if (!buckets.TryGetValue(key, out List<CombineInstance> list))
			{
				list = new List<CombineInstance>();
				buckets[key] = list;
			}
			list.Add(new CombineInstance
			{
				mesh = mf.sharedMesh,
				transform = mf.transform.localToWorldMatrix,
				subMeshIndex = 0
			});
			count++;
		}
		return count;
	}

	private static void DisableRenderersUnder(Transform root)
	{
		if (root == null) return;
		Renderer[] rends = root.GetComponentsInChildren<Renderer>(includeInactive: false);
		foreach (Renderer r in rends) r.enabled = false;
	}

	// Struct key cho dict — tránh boxing tuple.
	private readonly struct BucketKey : System.IEquatable<BucketKey>
	{
		public readonly Material Material;
		public readonly int CellX;
		public readonly int CellZ;
		public BucketKey(Material material, int cellX, int cellZ)
		{
			Material = material; CellX = cellX; CellZ = cellZ;
		}
		public bool Equals(BucketKey other) =>
			ReferenceEquals(Material, other.Material) && CellX == other.CellX && CellZ == other.CellZ;
		public override bool Equals(object obj) => obj is BucketKey k && Equals(k);
		public override int GetHashCode()
		{
			int h = Material != null ? Material.GetInstanceID() : 0;
			h = h * 397 ^ CellX;
			h = h * 397 ^ CellZ;
			return h;
		}
	}
}
