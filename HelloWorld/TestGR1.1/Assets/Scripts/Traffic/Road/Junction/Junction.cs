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

	public List<Vector3> CreatePrismVertices(List<Vector3> baseVertices, Vector3 heightVec)
	{
		List<Vector3> vertices = new List<Vector3>();
		float avgX = 0;
		float avgY = 0;
		float avgZ = 0;
		foreach (Vector3 baseVertex in baseVertices)
		{
			avgX += baseVertex.x;
			avgY += baseVertex.y;
			avgZ += baseVertex.z;
		}
		avgX /= baseVertices.Count;
		avgY /= baseVertices.Count;
		avgZ /= baseVertices.Count;
		Vector3 center = new Vector3(avgX, avgY, avgZ);

		vertices.Add(center);
		foreach (Vector3 baseVertex in baseVertices)
		{
			vertices.Add(baseVertex);
		}
		vertices.Add(center + heightVec);
		foreach (Vector3 baseVertex in baseVertices)
		{
			vertices.Add(baseVertex + heightVec);
		}
		return vertices;
	}

	public List<int> CreatePrismTriangles(int baseEdgeCount)
	{
		List<int> triangles = new List<int>();
		// Upper face
		for (int i = 1; i <= baseEdgeCount; i++)
		{
			triangles.Add(0);
			triangles.Add(i);
			if (i + 1 > baseEdgeCount)
			{
				triangles.Add((i + 1) % baseEdgeCount);
			}
			else
			{
				triangles.Add(i + 1);
			}
		}
		// Lower face
		for (int i = 1; i <= baseEdgeCount; i++)
		{
			triangles.Add(baseEdgeCount + 1);
			if (i + 1 > baseEdgeCount)
			{
				triangles.Add(baseEdgeCount + 2);
			}
			else
			{
				triangles.Add(i + baseEdgeCount + 2);
			}
			triangles.Add(i + baseEdgeCount + 1);
		}
		// Side faces
		for (int i = 1; i <= baseEdgeCount; i++)
		{
			int next = (i % baseEdgeCount) + 1;
			triangles.Add(i);
			triangles.Add(i + baseEdgeCount + 1);
			triangles.Add(next);

			triangles.Add(next + baseEdgeCount + 1);
			triangles.Add(next);
			triangles.Add(i + baseEdgeCount + 1);
		}
		return triangles;
	}

	public void Create(Vector3[] baseVertices, Vector3 heightVec, string id)
	{
		this.id = id;
		if (baseVertices == null || baseVertices.Length < 3)
		{
			return;
		}

		mesh = new Mesh();
		if (meshFilter == null) meshFilter = GetComponent<MeshFilter>();
		meshFilter.mesh = mesh;
		List<Vector3> vertices = CreatePrismVertices(new List<Vector3>(baseVertices), heightVec);
		List<int> triangles = CreatePrismTriangles(baseVertices.Length);
		mesh.Clear();
		mesh.vertices = vertices.ToArray();
		mesh.triangles = triangles.ToArray();
		mesh.RecalculateNormals();

		// Convex BoxCollider để Rigidbody/trigger không bị PhysX QuickHull lỗi với mesh phức tạp.
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
}
