using UnityEngine;
using System.Collections.Generic;

[RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
public class Junction : MonoBehaviour
{
	private string id = null;
	private Mesh mesh;
    [SerializeField] private MeshFilter meshFilter;
	public List<Vector3> baseVertices;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		//Create(baseVertices.ToArray(), new Vector3(0, -1, 0));
	}


	public List<Vector3> CreatePrismVertices(List<Vector3> baseVertices, Vector3 heightVec)
	{
		List<Vector3> vertices = new List<Vector3>();
		float avgX = 0;
		float avgZ = 0;
		foreach (Vector3 baseVertex in baseVertices)
		{
			avgX += baseVertex.x;
			avgZ += baseVertex.z;
		}
		avgX /= baseVertices.Count;
		avgZ /= baseVertices.Count;
		Vector3 center = new Vector3(avgX, 0, avgZ);
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
				triangles.Add((i+1)% baseEdgeCount);
			}
			else
			{
				triangles.Add(i + 1);
			}
		}
		//Lower face
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
		if (this.id == null)
		{
			this.id = id;
		}
		mesh = new Mesh();
		meshFilter.mesh = mesh;
		List<Vector3> vertices = CreatePrismVertices(new List<Vector3>(baseVertices), heightVec);
		List<int> triangles = CreatePrismTriangles(baseVertices.Length);
		mesh.Clear();
		mesh.vertices = vertices.ToArray();
		mesh.triangles = triangles.ToArray();
		mesh.RecalculateNormals();
	}
	public string GetId()
	{
		return id;
	}


	//private List<int> CreatePrismTriangles(int baseEdgeCount)
	//{
	//	List<int> triangles = new List<int>();
	//	// Upper face
	//	for (int i = 0; i < baseEdgeCount - 2; i++)
	//	{
	//		triangles.Add(0);
	//		triangles.Add(i + 1);
	//		triangles.Add(i + 2);
	//	}
	//	// Lower face
	//	for (int i = 0; i < baseEdgeCount - 2; i++)
	//	{
	//		triangles.Add(baseEdgeCount);
	//		triangles.Add(i + 2 + baseEdgeCount);
	//		triangles.Add(i + 1 + baseEdgeCount);
	//	}
	//	// Side faces
	//	for (int i = 0; i < baseEdgeCount; i++)
	//	{
	//		int next = (i + 1) % baseEdgeCount;
	//		triangles.Add(i);
	//		triangles.Add(i + baseEdgeCount);
	//		triangles.Add(next);

	//		triangles.Add(next + baseEdgeCount);
	//		triangles.Add(next);
	//		triangles.Add(i + baseEdgeCount);
	//	}
	//	return triangles;
	//}
	//private List<Vector3> CreatePrismVertices(Vector3[] baseVertices, Vector3 heightVec)
	//{
	//	List<Vector3> vertices = new List<Vector3>();
	//	foreach (Vector3 baseVertex in baseVertices)
	//	{
	//		vertices.Add(baseVertex);
	//	}
	//	foreach (Vector3 baseVertex in baseVertices)
	//	{
	//		vertices.Add(baseVertex + heightVec);
	//	}
	//	return vertices;
	//}
	//private List<Vector2> CreateUV(Vector3[] vertices)
	//{
	//	List<Vector2> uv = new List<Vector2>();
	//	foreach (Vector3 vertex in vertices)
	//	{
	//		uv.Add(new Vector2(vertex.x, vertex.z));
	//	}
	//	return uv;
	//}
}
