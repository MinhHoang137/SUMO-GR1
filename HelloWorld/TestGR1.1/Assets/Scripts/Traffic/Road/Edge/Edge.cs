using System;
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

	private string id;
	private EdgeData data;

	[Header("Lane materials")]
	[SerializeField] private LaneMaterialEntry[] laneMaterials;
	[SerializeField] private Material fallbackMaterial;

	[Header("Junction fit")]
	// Server đã snap lane endpoint vào biên polygon junction (xem edgeType0._snap_to_polygon).
	// Overshoot ở đây chỉ là safety margin để chống z-fight tại seam lane↔junction cùng cao độ.
	// Đặt 0 nếu material/độ cao tách bạch và không có z-fight; tăng nếu data lỗi vẫn còn gap.
	[SerializeField, Range(0f, 5f)] private float endpointOvershoot = 0.1f;

	[Header("Lane markings (vạch phân làn)")]
	// Để null nếu không muốn vẽ. Khi có material, vẽ vạch trắng giữa các cặp lane liền kề
	// (bỏ qua lane pedestrian — giữa vỉa hè và đường không phải vạch phân làn).
	[SerializeField] private Material laneMarkingMaterial;
	[SerializeField, Range(0.05f, 0.5f)] private float laneMarkingWidth = 0.15f;
	// Khoảng cách Y vạch nổi trên mặt đường — đủ nhỏ để không thấy độ dày, đủ lớn để không z-fight.
	[SerializeField, Range(0f, 0.01f)] private float laneMarkingYOffset = 0.005f;
	// Đặt gapLength = 0 (hoặc dashLength = 0) → vạch liền. Mặc định 2m dash + 4m gap (chuẩn đô thị).
	[SerializeField, Min(0f)] private float laneMarkingDashLength = 2.0f;
	[SerializeField, Min(0f)] private float laneMarkingGapLength = 4.0f;

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
}
