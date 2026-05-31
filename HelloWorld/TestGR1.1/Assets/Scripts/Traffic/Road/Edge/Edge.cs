using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Edge : Road
{
	[Serializable]
	public class LaneMaterialEntry
	{
		public string type;
		public Material material;
	}

	[SerializeField] private string id;
	private EdgeData data;

	[Header("Lane materials")]
	[Tooltip("Material cho từng loại lane (driving, sidewalk, pedestrian...). Key match theo Lane.type từ server.")]
	[SerializeField] private LaneMaterialEntry[] laneMaterials;
	[Tooltip("Material dùng khi lane.type không tìm thấy trong danh sách trên.")]
	[SerializeField] private Material fallbackMaterial;

	[Header("Junction fit")]
	[Tooltip("Kéo dài mesh dọc trục lane một đoạn (mét) để khớp biên junction theo phương ngang và chống z-fight tại seam. " +
	         "Tăng nếu thấy khe hở giữa lane và junction; đặt 0 nếu thấy overshoot. " +
	         "Server chỉ snap Z lane endpoint vào junction (không snap XY) để tránh rút mesh sidewalk + chồng lane 2 chiều.")]
	[SerializeField, Range(0f, 5f)] private float endpointOvershoot = 0.1f;

	[Header("Lane markings (vạch phân làn)")]
	[Tooltip("Material vẽ vạch trắng phân làn (giữa các cặp lane liền kề + biên trái edge). " +
	         "Để None nếu không muốn vẽ vạch.")]
	[SerializeField] private Material laneMarkingMaterial;
	[Tooltip("Bề rộng vạch phân làn (mét).")]
	[SerializeField, Range(0.05f, 0.5f)] private float laneMarkingWidth = 0.15f;
	[Tooltip("Khoảng cách Y vạch nổi trên mặt đường (mét). Đủ nhỏ để không thấy độ dày, đủ lớn để không z-fight.")]
	[SerializeField, Range(0f, 0.01f)] private float laneMarkingYOffset = 0.005f;
	[Tooltip("Chiều dài mỗi nét đứt của vạch (mét). Đặt 0 (hoặc gap = 0) để vạch liền. Mặc định 2m (chuẩn đô thị).")]
	[SerializeField, Min(0f)] private float laneMarkingDashLength = 2.0f;
	[Tooltip("Khoảng trống giữa các nét đứt (mét). Đặt 0 (hoặc dash = 0) để vạch liền. Mặc định 4m (chuẩn đô thị).")]
	[SerializeField, Min(0f)] private float laneMarkingGapLength = 4.0f;

	[Header("Lane colliders")]
	[Tooltip("Bật để dựng box collider cho cả edge: 1 sàn nằm phẳng (rộng = tổng width tất cả lane) + " +
	         "2 vách dựng đứng ở 2 biên ngoài. Mỗi segment polyline → 1 bộ 3 collider chung 1 GameObject con. " +
	         "Xe Unity có thể chạy + đổi làn tự do trong lòng edge.")]
	[SerializeField] private bool buildLaneColliders = true;
	[Tooltip("Bề dày tấm sàn collider (trục Y, mét). Mỏng cho collision chính xác, đủ dày tránh xuyên do float error.")]
	[SerializeField, Range(0.001f, 0.5f)] private float laneFloorThickness = 0.1f;
	[Tooltip("Bề dày vách collider (trục ngang lane, mét). Mỏng đủ để không lấn vào lane bên cạnh.")]
	[SerializeField, Range(0.001f, 0.5f)] private float laneWallThickness = 0.1f;
	[Tooltip("Chiều cao vách collider (mét). Default 2.")]
	[SerializeField, Range(0f, 5f)] private float laneWallHeight = 2.0f;
	[Tooltip("Rút ngắn vách collider mỗi đầu (mét) dọc theo segment. Tránh đầu mút vách chụm/lấn vào " +
	         "vách edge khác ở góc cua + junction khiến prune xoá nhầm → giữ được vách dọc. Sàn giữ nguyên chiều dài.")]
	[SerializeField, Range(0f, 2f)] private float laneWallEndInset = 1.0f;
	[Tooltip("Raycast từ mỗi vách ra ngoài đoạn này (mét). Nếu trúng collider khác → xoá collider đó + bỏ vách này " +
	         "→ giữa 2 edge sát nhau không còn vách trùng. Edge build sau sẽ detect vách edge build trước và xoá đi.")]
	[SerializeField, Range(0f, 1f)] private float wallProximityCheckDistance = 0.5f;

	public string GetId() => id;
	public EdgeData GetData() => data;

	public void Create(EdgeData edgeData)
	{
		if (edgeData == null || edgeData.lanes == null || edgeData.lanes.Count == 0)
		{
			return;
		}

		Lane baseLane = edgeData.lanes[0];
		if (baseLane.points == null || baseLane.points.Count == 0)
		{
			return;
		}

		id = edgeData.id;
		data = edgeData;

		// Origin Edge = điểm đầu lane đầu tiên (world space). Server đã emit `edgeData.position`
		// trỏ tới chính giá trị này (xem edgeType0.read_edges), nên dùng thẳng cho khỏi lặp.
		// Mesh vertex tính tương đối với origin (Unity convention). Khớp pattern Junction.cs.
		Vector3 origin = Converter.ToVector3(edgeData.position);
		transform.position = origin;

		for (int i = 0; i < edgeData.lanes.Count; i++)
		{
			BuildLane(edgeData.lanes[i], i, origin);
		}

		BuildLaneMarkings(edgeData, origin);
		BuildLeftEdgeLine(edgeData, origin);
		BuildLaneColliders(edgeData, origin);
	}

	private void BuildLane(Lane lane, int index, Vector3 origin)
	{
		if (lane == null || lane.points == null || lane.points.Count < 2)
		{
			return;
		}

		GameObject laneGO = new GameObject($"Lane_{index}_{lane.type}");
		laneGO.transform.SetParent(transform, worldPositionStays: false);

		MeshFilter mf = laneGO.AddComponent<MeshFilter>();
		MeshRenderer mr = laneGO.AddComponent<MeshRenderer>();
		mr.sharedMaterial = GetMaterialFor(lane.type);

		Mesh mesh = new Mesh();
		mesh.SetVertices(BuildLaneVertices(lane, origin));
		mesh.SetTriangles(BuildLaneTriangles(lane.points.Count), 0);
		mesh.RecalculateNormals();
		mf.mesh = mesh;
	}

	private List<Vector3> BuildLaneVertices(Lane lane, Vector3 origin)
	{
		List<Vector3> vertices = new List<Vector3>();
		int pointCnt = lane.points.Count;
		float halfWidth = lane.width / 2f;

		for (int i = 0; i < pointCnt; i++)
		{
			Vector3 pt = Converter.ToVector3(lane.points[i]);

			Vector3 right;
			float dist = halfWidth;

			if (i == 0)
			{
				Vector3 dir = Converter.ToVector3(lane.points[i + 1]) - pt;
				Vector3 dirN = dir.normalized;
				right = Vector3.Cross(dirN, -Vector3.up);
				// Lùi safety margin chống z-fight; snap chính đã làm server-side.
				pt -= dirN * endpointOvershoot;
			}
			else if (i == pointCnt - 1)
			{
				Vector3 dir = pt - Converter.ToVector3(lane.points[i - 1]);
				Vector3 dirN = dir.normalized;
				right = Vector3.Cross(dirN, -Vector3.up);
				pt += dirN * endpointOvershoot;
			}
			else
			{
				Vector3 toMid = pt - Converter.ToVector3(lane.points[i - 1]);
				Vector3 fromMid = Converter.ToVector3(lane.points[i + 1]) - pt;
				Vector3 midDir = ((toMid.normalized + fromMid.normalized) / 2f).normalized;
				right = Vector3.Cross(midDir, -Vector3.up);
				// scale theo cos góc giữa hai đoạn để mesh không bị bóp lại khi đường cong.
				float angleRad = Vector3.Angle(toMid, fromMid) / 2f * Mathf.Deg2Rad;
				float cosA = Mathf.Cos(angleRad);
				if (cosA > 0.01f) dist = halfWidth / cosA;
			}

			// Subtract origin → vertex ở local space của Edge GameObject (đặt tại origin).
			// Toán intermediate (dir, right, dist) translation-invariant nên không bị ảnh hưởng.
			vertices.Add(pt + right * dist - origin);
			vertices.Add(pt - right * dist - origin);
		}
		return vertices;
	}

	private List<int> BuildLaneTriangles(int pointCnt)
	{
		List<int> triangles = new List<int>();
		for (int i = 0; i < pointCnt - 1; i++)
		{
			triangles.Add(2 * i);
			triangles.Add(2 * i + 1);
			triangles.Add(2 * i + 2);

			triangles.Add(2 * i + 1);
			triangles.Add(2 * i + 3);
			triangles.Add(2 * i + 2);
		}
		return triangles;
	}

	// Vẽ vạch trắng giữa mọi cặp lane liền kề (bao gồm cả ranh giới vỉa hè ↔ lòng đường —
	// ngoài đời cũng có vạch trắng liền ở đó). Hầu hết edge OSM chỉ có 2 lane (sidewalk +
	// 1 lane xe), nếu skip pedestrian thì sẽ không có vạch nào.
	private void BuildLaneMarkings(EdgeData edgeData, Vector3 origin)
	{
		if (laneMarkingMaterial == null) return;
		var lanes = edgeData.lanes;
		for (int i = 0; i < lanes.Count - 1; i++)
		{
			Lane a = lanes[i];
			Lane b = lanes[i + 1];
			if (a == null || b == null) continue;
			if (a.points == null || a.points.Count < 2) continue;
			BuildSingleMarking(a, i, origin);
		}
	}

	// Vẽ vạch liền ở biên ngoài cùng bên trái của edge (= biên trái của lane cuối).
	// Cho 2-way road model dạng 2 edge cạnh nhau (X, -X), 2 vạch của 2 edge gặp nhau ở giữa
	// → nhìn như center divider mà không cần server biết về cặp đảo chiều.
	// Skip nếu lane cuối là pedestrian (tránh vẽ đường ngoài rìa vỉa hè).
	private void BuildLeftEdgeLine(EdgeData edgeData, Vector3 origin)
	{
		if (laneMarkingMaterial == null) return;
		var lanes = edgeData.lanes;
		Lane leftmost = lanes[^1];
		if (leftmost == null || leftmost.points == null || leftmost.points.Count < 2) return;
		if (leftmost.type == "pedestrian") return;

		BuildSingleMarking(leftmost, lanes.Count - 1, origin, forceSolid: true, namePrefix: "EdgeLine");
	}

	private void BuildSingleMarking(Lane lane, int laneIndex, Vector3 origin,
	                                bool forceSolid = false, string namePrefix = "Marking")
	{
		ComputeMarkingBoundary(lane, out Vector3[] boundaryPts, out Vector3[] rights);

		string goName = forceSolid ? namePrefix : $"{namePrefix}_{laneIndex}-{laneIndex + 1}";
		GameObject go = new GameObject(goName);
		go.transform.SetParent(transform, worldPositionStays: false);
		MeshFilter mf = go.AddComponent<MeshFilter>();
		MeshRenderer mr = go.AddComponent<MeshRenderer>();
		mr.sharedMaterial = laneMarkingMaterial;

		Mesh mesh = new Mesh();
		bool dashed = !forceSolid && laneMarkingDashLength > 0f && laneMarkingGapLength > 0f;
		if (dashed)
		{
			BuildDashedMarkingMesh(mesh, boundaryPts, rights, origin);
		}
		else
		{
			BuildSolidMarkingMesh(mesh, boundaryPts, rights, origin);
		}
		mesh.RecalculateNormals();
		mf.mesh = mesh;
	}

	// Tính centerline của vạch (giữa lane[i] và lane[i+1]) + right vector tại mỗi vertex polyline.
	// SUMO convention: lane 0 = rightmost trong direction of travel → biên trái lane[i] = boundary.
	// Nếu chạy data left-hand-traffic và vạch lệch ngoài, đảo dấu `pt - right` → `pt + right`.
	private void ComputeMarkingBoundary(Lane lane, out Vector3[] boundaryPts, out Vector3[] rights)
	{
		int n = lane.points.Count;
		boundaryPts = new Vector3[n];
		rights = new Vector3[n];
		float laneHalfWidth = lane.width / 2f;
		Vector3 yOffset = Vector3.up * laneMarkingYOffset;

		for (int i = 0; i < n; i++)
		{
			Vector3 pt = Converter.ToVector3(lane.points[i]);
			Vector3 right;
			float laneDist = laneHalfWidth;

			if (i == 0)
			{
				Vector3 dirN = (Converter.ToVector3(lane.points[i + 1]) - pt).normalized;
				right = Vector3.Cross(dirN, -Vector3.up);
			}
			else if (i == n - 1)
			{
				Vector3 dirN = (pt - Converter.ToVector3(lane.points[i - 1])).normalized;
				right = Vector3.Cross(dirN, -Vector3.up);
			}
			else
			{
				Vector3 toMid = pt - Converter.ToVector3(lane.points[i - 1]);
				Vector3 fromMid = Converter.ToVector3(lane.points[i + 1]) - pt;
				Vector3 midDir = ((toMid.normalized + fromMid.normalized) / 2f).normalized;
				right = Vector3.Cross(midDir, -Vector3.up);
				float angleRad = Vector3.Angle(toMid, fromMid) / 2f * Mathf.Deg2Rad;
				float cosA = Mathf.Cos(angleRad);
				if (cosA > 0.01f) laneDist = laneHalfWidth / cosA;
			}

			boundaryPts[i] = pt - right * laneDist + yOffset;
			rights[i] = right;
		}
	}

	private void BuildSolidMarkingMesh(Mesh mesh, Vector3[] boundaryPts, Vector3[] rights, Vector3 origin)
	{
		int n = boundaryPts.Length;
		float markHalfWidth = laneMarkingWidth / 2f;
		List<Vector3> verts = new List<Vector3>(n * 2);
		for (int i = 0; i < n; i++)
		{
			verts.Add(boundaryPts[i] + rights[i] * markHalfWidth - origin);
			verts.Add(boundaryPts[i] - rights[i] * markHalfWidth - origin);
		}
		mesh.SetVertices(verts);
		mesh.SetTriangles(BuildLaneTriangles(n), 0);
	}

	// Vạch đứt đoạn: walk polyline theo arc length, chu kỳ (dash + gap). Mỗi dash = 1 quad
	// thẳng từ điểm bắt đầu tới điểm kết thúc, tính position + right bằng interpolation tuyến
	// tính dọc segment polyline. Trên đoạn cong gắt, dash dài có thể cắt corner — chấp nhận
	// được vì dash thường ngắn (2m) so với segment polyline (>5m).
	private void BuildDashedMarkingMesh(Mesh mesh, Vector3[] boundaryPts, Vector3[] rights, Vector3 origin)
	{
		int n = boundaryPts.Length;
		if (n < 2) { mesh.Clear(); return; }

		float[] cumLen = new float[n];
		for (int i = 1; i < n; i++)
		{
			cumLen[i] = cumLen[i - 1] + Vector3.Distance(boundaryPts[i - 1], boundaryPts[i]);
		}
		float totalLen = cumLen[n - 1];
		if (totalLen <= 0f) { mesh.Clear(); return; }

		float markHalfWidth = laneMarkingWidth / 2f;
		float period = laneMarkingDashLength + laneMarkingGapLength;
		List<Vector3> verts = new List<Vector3>();
		List<int> tris = new List<int>();

		for (float cursor = 0f; cursor < totalLen; cursor += period)
		{
			float dashStart = cursor;
			float dashEnd = Mathf.Min(cursor + laneMarkingDashLength, totalLen);
			if (dashEnd - dashStart < 1e-4f) continue;

			InterpolateAt(cumLen, boundaryPts, rights, dashStart, out Vector3 sPos, out Vector3 sRight);
			InterpolateAt(cumLen, boundaryPts, rights, dashEnd, out Vector3 ePos, out Vector3 eRight);

			int b = verts.Count;
			verts.Add(sPos + sRight * markHalfWidth - origin);
			verts.Add(sPos - sRight * markHalfWidth - origin);
			verts.Add(ePos + eRight * markHalfWidth - origin);
			verts.Add(ePos - eRight * markHalfWidth - origin);
			// Cùng pattern winding với BuildLaneTriangles cho strip 2-point.
			tris.Add(b); tris.Add(b + 1); tris.Add(b + 2);
			tris.Add(b + 1); tris.Add(b + 3); tris.Add(b + 2);
		}

		mesh.SetVertices(verts);
		mesh.SetTriangles(tris, 0);
	}

	private static void InterpolateAt(float[] cumLen, Vector3[] pts, Vector3[] rights, float target,
	                                  out Vector3 pos, out Vector3 right)
	{
		int n = cumLen.Length;
		if (target <= 0f) { pos = pts[0]; right = rights[0]; return; }
		if (target >= cumLen[n - 1]) { pos = pts[n - 1]; right = rights[n - 1]; return; }
		for (int i = 1; i < n; i++)
		{
			if (target <= cumLen[i])
			{
				float seg = cumLen[i] - cumLen[i - 1];
				float t = seg > 1e-9f ? (target - cumLen[i - 1]) / seg : 0f;
				pos = Vector3.Lerp(pts[i - 1], pts[i], t);
				// Slerp giữ độ dài unit; right vector luôn unit length.
				right = Vector3.Slerp(rights[i - 1], rights[i], t).normalized;
				return;
			}
		}
		pos = pts[n - 1]; right = rights[n - 1];
	}

	private Material GetMaterialFor(string type)
	{
		if (laneMaterials != null)
		{
			foreach (var entry in laneMaterials)
			{
				if (entry != null && entry.type == type) return entry.material;
			}
		}
		return fallbackMaterial;
	}

	// Dựng collider cho TOÀN edge (không chia theo lane) — để xe Unity có thể chạy và đổi làn
	// tự do trong lòng đường. Mỗi segment polyline có hướng khác nhau, mà BoxCollider lấy
	// rotation từ Transform của GameObject → buộc phải có 1 GameObject con / segment.
	// Tối ưu: 3 collider (sàn + 2 vách) cùng segment dùng chung Transform đó, phân biệt nhau
	// bằng BoxCollider.center + size (axis local: X = ngang, Y = đứng, Z = dọc segment).
	// Spine = polyline lane[0] (rightmost theo SUMO). Centerline edge dịch -right khỏi spine
	// một đoạn = (totalEdgeWidth - lane0.width) / 2.
	private void BuildLaneColliders(EdgeData edgeData, Vector3 origin)
	{
		if (!buildLaneColliders) return;
		var lanes = edgeData.lanes;
		if (lanes == null || lanes.Count == 0) return;

		Lane spineLane = lanes[0];
		if (spineLane == null || spineLane.points == null || spineLane.points.Count < 2) return;

		float totalEdgeWidth = 0f;
		for (int i = 0; i < lanes.Count; i++) totalEdgeWidth += lanes[i].width;
		float halfEdgeWidth = totalEdgeWidth * 0.5f;
		float spineToEdgeCenterOffset = halfEdgeWidth - spineLane.width * 0.5f;
		float halfWallHeight = laneWallHeight * 0.5f;

		GameObject collidersRoot = new("EdgeColliders");
		collidersRoot.transform.SetParent(transform, worldPositionStays: false);

		// Track tất cả vách đã dựng để dọn ở pass sau (1 frame delay). Build pass này tránh
		// raycast vì collider mới AddComponent chưa được physics world thấy ngay trong cùng frame
		// (autoSyncTransforms = false từ Unity 2018.3+). Delay 1 frame đảm bảo TẤT CẢ edge đã build
		// xong → cleanup symmetric, không phụ thuộc thứ tự build edge nào trước.
		List<BoxCollider> builtWalls = new();

		int segmentCount = spineLane.points.Count - 1;
		for (int segmentIndex = 0; segmentIndex < segmentCount; segmentIndex++)
		{
			Vector3 spineStart = Converter.ToVector3(spineLane.points[segmentIndex]);
			Vector3 spineEnd = Converter.ToVector3(spineLane.points[segmentIndex + 1]);
			Vector3 segmentVector = spineEnd - spineStart;
			float segmentLength = segmentVector.magnitude;
			if (segmentLength < 1e-4f) continue;

			// Vách rút ngắn mỗi đầu để đầu mút không chạm vách lân cận (góc cua / junction) khiến
			// prune xoá nhầm. Clamp tối thiểu để segment ngắn vẫn còn 1 đoạn vách.
			float wallLength = Mathf.Max(segmentLength - 2f * laneWallEndInset, 0.1f);

			Vector3 segmentDirection = segmentVector / segmentLength;
			// Cùng convention với BuildLaneVertices: right = Cross(dir, -up).
			// +right = về phía lane index nhỏ hơn; -right = về phía lane index lớn hơn.
			Vector3 segmentRight = Vector3.Cross(segmentDirection, -Vector3.up);

			Vector3 spineMidpoint = (spineStart + spineEnd) * 0.5f;
			Vector3 edgeCenterLocal = spineMidpoint - segmentRight * spineToEdgeCenterOffset - origin;
			// LookRotation đặt trục Z local theo segmentDirection ⇒ trục X local = segmentRight, Y = up.
			Quaternion segmentRotation = Quaternion.LookRotation(segmentDirection, Vector3.up);

			GameObject segmentGO = new($"Segment_{segmentIndex}");
			segmentGO.transform.SetParent(collidersRoot.transform, worldPositionStays: false);
			segmentGO.transform.SetLocalPositionAndRotation(edgeCenterLocal, segmentRotation);

			// Floor — center tại gốc local (đã đặt ở edge center).
			AddBoxCollider(segmentGO,
				center: Vector3.zero,
				size: new Vector3(totalEdgeWidth, laneFloorThickness, segmentLength));

			// Vách phải — dịch +X local (= +segmentRight). Luôn build, track để pass cleanup sau lo.
			BoxCollider rightWall = AddBoxCollider(segmentGO,
				center: new Vector3(halfEdgeWidth, halfWallHeight, 0f),
				size: new Vector3(laneWallThickness, laneWallHeight, wallLength));
			builtWalls.Add(rightWall);

			// Vách trái — dịch -X local.
			BoxCollider leftWall = AddBoxCollider(segmentGO,
				center: new Vector3(-halfEdgeWidth, halfWallHeight, 0f),
				size: new Vector3(laneWallThickness, laneWallHeight, wallLength));
			builtWalls.Add(leftWall);
		}

		// Lên lịch dọn các cặp vách sát nhau ở frame sau — lúc đó physics đã sync và mọi edge khác
		// (nếu build cùng frame) cũng đã dựng xong walls của họ.
		StartCoroutine(PruneAdjacentWallsNextFrame(builtWalls));
	}

	// Pass cleanup chạy sau 1 frame. 3 phase, cache trước, destroy 1 lượt:
	//   (1) OverlapBox cho mỗi vách → bắt các vách CHỒNG / TOUCHING (raycast không tới vì
	//       Unity skip collider chứa origin).
	//   (2) Raycast outward CHỈ NGOÀI mặt ngoài vách → bắt các vách GẦN (≤ 0.5m) chưa chạm.
	//   (3) Iterate set toDestroy, disable + Destroy 1 lần.
	// Filter quan trọng: bỏ qua chính mình, vách cùng edge (myWalls), và floor (center.x ≈ 0).
	private IEnumerator PruneAdjacentWallsNextFrame(List<BoxCollider> walls)
	{
		yield return null;
		Physics.SyncTransforms();

		HashSet<BoxCollider> myWalls = new(walls);
		HashSet<BoxCollider> toDestroy = new();
		Collider[] overlapBuffer = new Collider[16];

		foreach (BoxCollider wall in walls)
		{
			if (wall == null) continue;

			Transform wallTransform = wall.transform;
			Vector3 worldCenter = wallTransform.TransformPoint(wall.center);
			Quaternion worldRotation = wallTransform.rotation;

			// (1) OverlapBox — bắt vách chồng/touching.
			Vector3 halfExtents = wall.size * 0.5f;
			int overlapCount = Physics.OverlapBoxNonAlloc(worldCenter, halfExtents, overlapBuffer, worldRotation);
			for (int k = 0; k < overlapCount; k++)
			{
				if (IsForeignWall(overlapBuffer[k], wall, myWalls, out BoxCollider foreignBox))
				{
					toDestroy.Add(wall);
					toDestroy.Add(foreignBox);
				}
			}

			// (2) Raycast outward — bắt vách gần chưa chạm. Offset origin ra ngoài mặt vách để
			// không vướng Unity skip-self-collider khi cast từ trong vách.
			Vector3 outwardLocal = wall.center.x > 0f ? Vector3.right : Vector3.left;
			Vector3 worldDirection = wallTransform.TransformDirection(outwardLocal);
			float originOffset = wall.size.x * 0.5f + 0.001f;
			Vector3 rayOrigin = worldCenter + worldDirection * originOffset;
			float rayDistance = wallProximityCheckDistance - originOffset;
			if (rayDistance <= 0f) continue;

			if (Physics.Raycast(rayOrigin, worldDirection, out RaycastHit hit, rayDistance)
			    && IsForeignWall(hit.collider, wall, myWalls, out BoxCollider rayHitBox))
			{
				toDestroy.Add(wall);
				toDestroy.Add(rayHitBox);
			}
		}

		// (3) Destroy tất cả 1 lượt.
		foreach (BoxCollider box in toDestroy)
		{
			if (box == null) continue;
			box.enabled = false;
			Destroy(box);
		}
	}

	// "Foreign wall" = BoxCollider của vách thuộc edge KHÁC.
	// Lọc: cùng object (self), cùng edge (myWalls set), floor (center.x ≈ 0), hoặc thuộc Junction
	// (junction có BoxCollider phủ toàn vùng giao lộ — không phải vách edge, đừng huỷ).
	private static bool IsForeignWall(Collider candidate, BoxCollider selfWall,
	                                  HashSet<BoxCollider> myWalls, out BoxCollider foreignWall)
	{
		foreignWall = null;
		if (candidate is not BoxCollider box) return false;
		if (box == selfWall) return false;
		if (myWalls.Contains(box)) return false;
		if (Mathf.Approximately(box.center.x, 0f)) return false;
		if (box.GetComponent<Junction>() != null) return false;
		foreignWall = box;
		return true;
	}

	private static BoxCollider AddBoxCollider(GameObject host, Vector3 center, Vector3 size)
	{
		BoxCollider boxCollider = host.AddComponent<BoxCollider>();
		boxCollider.center = center;
		boxCollider.size = size;
		return boxCollider;
	}
}
