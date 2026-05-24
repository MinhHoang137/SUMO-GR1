using UnityEngine;
using System.Collections.Generic;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class Junction : Road
{
	[SerializeField] private string id = null;
	private Mesh mesh;
	[SerializeField] private MeshFilter meshFilter;
	[SerializeField] private BoxCollider boxCollider;
	[SerializeField] private bool boxColliderIsTrigger = true;

	public List<Vector3> baseVertices;
	public JunctionData data;

	public void Create(Vector3[] baseVerticesArray, Vector3 heightVec, string id)
	{
		this.id = id;
		if (baseVerticesArray == null || baseVerticesArray.Length < 3)
		{
			return;
		}

		List<Vector3> polyVerts = new List<Vector3>(baseVerticesArray);
		EnsureClockwiseFromAbove(polyVerts);

		// Bước 1: thử ear clipping trên polygon gốc (giữ được detail concave).
		List<int> topTris = EarClipTriangulateXZ(polyVerts);
		int expectedIndices = (polyVerts.Count - 2) * 3;

		// Bước 2: nếu ear clipping bị stuck (polygon non-simple — SUMO cluster_xxx đôi khi emit
		// shape tự cắt vì join nhiều junction sát nhau), fallback convex hull. Mất một ít detail
		// concave nhưng đảm bảo mesh phủ đúng vùng junction, không bị "rách" như screenshot báo.
		if (topTris.Count < expectedIndices)
		{
			polyVerts = ConvexHullXZ(polyVerts);
			EnsureClockwiseFromAbove(polyVerts);
			topTris = EarClipTriangulateXZ(polyVerts);
		}

		int n = polyVerts.Count;

		// Vertex layout: [0..n-1] = top, [n..2n-1] = bottom (top + heightVec).
		Vector3[] vertices = new Vector3[2 * n];
		for (int i = 0; i < n; i++)
		{
			vertices[i] = polyVerts[i];
			vertices[i + n] = polyVerts[i] + heightVec;
		}

		List<int> triangles = new List<int>(topTris);

		// Bottom face: cùng triangulation, đảo winding để normal hướng -Y, dời index sang dải dưới.
		for (int i = 0; i < topTris.Count; i += 3)
		{
			triangles.Add(topTris[i] + n);
			triangles.Add(topTris[i + 2] + n);
			triangles.Add(topTris[i + 1] + n);
		}

		// Side faces (CW polygon → winding dưới đây cho normal hướng ra ngoài).
		for (int i = 0; i < n; i++)
		{
			int next = (i + 1) % n;
			triangles.Add(i);
			triangles.Add(i + n);
			triangles.Add(next);

			triangles.Add(next);
			triangles.Add(i + n);
			triangles.Add(next + n);
		}

		mesh = new Mesh();
		if (meshFilter == null) meshFilter = GetComponent<MeshFilter>();
		mesh.vertices = vertices;
		mesh.triangles = triangles.ToArray();
		mesh.RecalculateNormals();
		meshFilter.mesh = mesh;

		// Convex BoxCollider để PhysX không lỗi QuickHull với mesh concave.
		if (boxCollider == null)
		{
			boxCollider = GetComponent<BoxCollider>();
			if (boxCollider == null)
			{
				boxCollider = gameObject.AddComponent<BoxCollider>();
			}
		}

		Bounds b = mesh.bounds;
		boxCollider.center = b.center;
		boxCollider.size = new Vector3(
			Mathf.Max(b.size.x, 0.01f),
			Mathf.Max(b.size.y, 0.01f),
			Mathf.Max(b.size.z, 0.01f)
		);
		boxCollider.isTrigger = boxColliderIsTrigger;
	}

	public string GetId()
	{
		return id;
	}

	// === Geometry helpers ===

	// Chuẩn hoá polygon về thứ tự CW khi nhìn từ +Y xuống (Unity XZ).
	private static void EnsureClockwiseFromAbove(List<Vector3> verts)
	{
		int n = verts.Count;
		if (n < 3) return;
		float signed = 0f;
		for (int i = 0; i < n; i++)
		{
			Vector3 a = verts[i];
			Vector3 b = verts[(i + 1) % n];
			signed += (b.x - a.x) * (b.z + a.z);
		}
		if (signed < 0f) verts.Reverse();
	}

	// Ear clipping cho simple polygon (project xuống XZ).
	// Đầu vào: polygon CW. Đầu ra: list index tam giác winding CW → normal +Y.
	private static List<int> EarClipTriangulateXZ(List<Vector3> verts)
	{
		List<int> triangles = new List<int>();
		int n = verts.Count;
		if (n < 3) return triangles;

		List<int> indices = new List<int>(n);
		for (int i = 0; i < n; i++) indices.Add(i);

		int safety = n * n;
		while (indices.Count > 3 && safety-- > 0)
		{
			bool earFound = false;
			int count = indices.Count;
			for (int i = 0; i < count; i++)
			{
				int pi = (i - 1 + count) % count;
				int ni = (i + 1) % count;
				int pIdx = indices[pi];
				int cIdx = indices[i];
				int nIdx = indices[ni];
				Vector3 a = verts[pIdx];
				Vector3 b = verts[cIdx];
				Vector3 c = verts[nIdx];

				float cross = (b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x);
				if (cross >= 0f) continue;

				bool inside = false;
				for (int j = 0; j < count; j++)
				{
					if (j == pi || j == i || j == ni) continue;
					if (PointInTriangleXZ(verts[indices[j]], a, b, c))
					{
						inside = true;
						break;
					}
				}
				if (inside) continue;

				triangles.Add(pIdx);
				triangles.Add(cIdx);
				triangles.Add(nIdx);
				indices.RemoveAt(i);
				earFound = true;
				break;
			}
			if (!earFound) break;
		}
		if (indices.Count == 3)
		{
			triangles.Add(indices[0]);
			triangles.Add(indices[1]);
			triangles.Add(indices[2]);
		}
		return triangles;
	}

	// Andrew's monotone chain. Trả về convex hull (CCW chuẩn math, sẽ được EnsureClockwise sửa lại).
	// Y của từng vertex giữ nguyên — convex hull chỉ tính trên XZ. Nếu junction nằm trên dốc,
	// Y của hull vertex là Y của input vertex tương ứng (không nội suy).
	private static List<Vector3> ConvexHullXZ(List<Vector3> input)
	{
		List<Vector3> pts = new List<Vector3>(input);
		pts.Sort((a, b) =>
		{
			int cmp = a.x.CompareTo(b.x);
			return cmp != 0 ? cmp : a.z.CompareTo(b.z);
		});
		int n = pts.Count;
		if (n < 3) return pts;

		List<Vector3> hull = new List<Vector3>(2 * n);
		// Lower hull
		foreach (var p in pts)
		{
			while (hull.Count >= 2 && HullCrossXZ(hull[hull.Count - 2], hull[hull.Count - 1], p) <= 0f)
				hull.RemoveAt(hull.Count - 1);
			hull.Add(p);
		}
		// Upper hull
		int lowerLen = hull.Count + 1;
		for (int i = n - 2; i >= 0; i--)
		{
			var p = pts[i];
			while (hull.Count >= lowerLen && HullCrossXZ(hull[hull.Count - 2], hull[hull.Count - 1], p) <= 0f)
				hull.RemoveAt(hull.Count - 1);
			hull.Add(p);
		}
		hull.RemoveAt(hull.Count - 1);
		return hull;
	}

	private static float HullCrossXZ(Vector3 o, Vector3 a, Vector3 b)
	{
		return (a.x - o.x) * (b.z - o.z) - (a.z - o.z) * (b.x - o.x);
	}

	private static bool PointInTriangleXZ(Vector3 p, Vector3 a, Vector3 b, Vector3 c)
	{
		float d1 = SignXZ(p, a, b);
		float d2 = SignXZ(p, b, c);
		float d3 = SignXZ(p, c, a);
		bool hasNeg = d1 < 0f || d2 < 0f || d3 < 0f;
		bool hasPos = d1 > 0f || d2 > 0f || d3 > 0f;
		return !(hasNeg && hasPos);
	}

	private static float SignXZ(Vector3 p1, Vector3 p2, Vector3 p3)
	{
		return (p1.x - p3.x) * (p2.z - p3.z) - (p2.x - p3.x) * (p1.z - p3.z);
	}
}
