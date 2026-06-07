using UnityEngine;
using System.Collections.Generic;

/*
	Dựng mesh khối nhà bằng cách extrude polygon footprint (đáy, y≈0 cục bộ) lên cao
	`height`: mái ở trên (+Y), tường bao quanh, đáy ở dưới. Cùng kỹ thuật ear-clipping
	(fallback convex hull cho polygon non-simple) như Junction.cs — helper hình học được
	sao chép vào đây để Building độc lập, không ràng buộc vào Junction.
*/
[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class Building : MonoBehaviour
{
	[SerializeField] private string id = null;
	[SerializeField] private MeshFilter meshFilter;
	// Collider: dùng MeshCollider ôm sát hình khối. Khối nhà là static (không Rigidbody)
	// nên MeshCollider non-convex hợp lệ. Tắt nếu chỉ cần trang trí (nhẹ hơn).
	[SerializeField] private bool addCollider = true;
	[SerializeField] private MeshCollider meshCollider;
	private Mesh mesh;

	public List<Vector3> baseVertices;
	public BuildingData data;

	public void Create(Vector3[] baseVerticesArray, float height, string id)
	{
		this.id = id;
		if (baseVerticesArray == null || baseVerticesArray.Length < 3 || height <= 0f)
		{
			return;
		}

		List<Vector3> polyVerts = new List<Vector3>(baseVerticesArray);
		EnsureClockwiseFromAbove(polyVerts);

		// Ear clipping trên polygon gốc; nếu stuck (polygon tự cắt) → convex hull.
		List<int> roofTris = EarClipTriangulateXZ(polyVerts);
		int expectedIndices = (polyVerts.Count - 2) * 3;
		if (roofTris.Count < expectedIndices)
		{
			polyVerts = ConvexHullXZ(polyVerts);
			EnsureClockwiseFromAbove(polyVerts);
			roofTris = EarClipTriangulateXZ(polyVerts);
		}

		int n = polyVerts.Count;
		Vector3 up = new Vector3(0f, height, 0f);

		// Vertex layout: [0..n-1] = mái (đáy nâng lên +height), [n..2n-1] = nền (y≈0).
		Vector3[] vertices = new Vector3[2 * n];
		for (int i = 0; i < n; i++)
		{
			vertices[i] = polyVerts[i] + up;
			vertices[i + n] = polyVerts[i];
		}

		List<int> triangles = new List<int>(roofTris);

		// Đáy: cùng triangulation, đảo winding (normal -Y), dời index sang dải nền.
		for (int i = 0; i < roofTris.Count; i += 3)
		{
			triangles.Add(roofTris[i] + n);
			triangles.Add(roofTris[i + 2] + n);
			triangles.Add(roofTris[i + 1] + n);
		}

		// Tường: polygon CW → winding dưới cho normal hướng ra ngoài.
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
		mesh.RecalculateBounds();
		meshFilter.mesh = mesh;

		if (addCollider)
		{
			if (meshCollider == null)
			{
				meshCollider = GetComponent<MeshCollider>();
				if (meshCollider == null) meshCollider = gameObject.AddComponent<MeshCollider>();
			}
			// Static, non-convex: ôm sát tường/mái. sharedMesh = mesh vừa dựng.
			meshCollider.convex = false;
			meshCollider.sharedMesh = mesh;
		}
	}

	public string GetId()
	{
		return id;
	}

	public void SetMaterial(Material material)
	{
		if (material == null) return;
		var renderer = GetComponent<MeshRenderer>();
		if (renderer != null) renderer.sharedMaterial = material;
	}

	// === Geometry helpers (sao chép từ Junction.cs để Building độc lập) ===

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
		foreach (var p in pts)
		{
			while (hull.Count >= 2 && HullCrossXZ(hull[hull.Count - 2], hull[hull.Count - 1], p) <= 0f)
				hull.RemoveAt(hull.Count - 1);
			hull.Add(p);
		}
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
