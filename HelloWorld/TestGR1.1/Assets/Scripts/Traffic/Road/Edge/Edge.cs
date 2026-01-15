using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Security.Cryptography.X509Certificates;
using UnityEngine;

public class Edge : Road // edgeType_0
{
	private string id;
    [SerializeField] private Transform walkingLanePrefab;
	[SerializeField] private Transform[] treePrefabs;
	[SerializeField] private RoadLane roadLanePrefab;
	[SerializeField] private MeshFilter meshFilter;

	[SerializeField] private EdgeData data;

    public List<Vector3> BuildVertices(EdgeData edgeData)
    {
		List<Vector3> vertices = new List<Vector3>();
		Lane baseLane = edgeData.lanes[0];	
		int laneCount = edgeData.lanes.Count;
		int pointCnt = baseLane.points.Count;
		float laneWidth = baseLane.width;

		Vector3 right;
		Vector3 left;
		Vector3 vertex;
		float openWidth;

		for (int i = 0; i < pointCnt; i++)
		{
			// first point
			if (i == 0 && pointCnt > 1)
			{ 
				// get direction vector
				Vector3 dir = Converter.ToVector3(baseLane.points[i + 1]) - Converter.ToVector3(baseLane.points[i]);
				
				// open to the right side
				right = Vector3.Cross(dir.normalized, -Vector3.up);
				vertex = Converter.ToVector3(baseLane.points[i]) + right * laneWidth / 2;
				vertices.Add(vertex);

				// open to the left side
				left = -right;
                openWidth = laneWidth * ((float)laneCount - 0.5f);
				vertex = Converter.ToVector3(baseLane.points[i]) + left * openWidth;
				vertices.Add(vertex);
				continue;
			}

			// last point
			if (i == pointCnt - 1)
			{
				// get direction vector
				Vector3 dir = Converter.ToVector3(baseLane.points[i]) - Converter.ToVector3(baseLane.points[i - 1]);

				// open to the right side
				right = Vector3.Cross(dir.normalized, -Vector3.up);
				vertex = Converter.ToVector3(baseLane.points[i]) + right * laneWidth / 2;
				vertices.Add(vertex);

				// open to the left side
				left = -right;
				openWidth = laneWidth * ((float)laneCount - 0.5f);
				vertex = Converter.ToVector3(baseLane.points[i]) + left * openWidth;
				vertices.Add(vertex);
				continue;
			}

			// middle points
			Vector3 toMid = Converter.ToVector3(baseLane.points[i]) - Converter.ToVector3(baseLane.points[i - 1]);
			Vector3 fromMid = Converter.ToVector3(baseLane.points[i + 1]) - Converter.ToVector3(baseLane.points[i]);
			Vector3 midDir = ((toMid.normalized + fromMid.normalized)/2).normalized;
			Vector3 openDir = Vector3.Cross(midDir, -Vector3.up);
			float angleRad = Vector3.Angle(toMid, fromMid) / 2f * Mathf.Deg2Rad;
			float openUnit = laneWidth / Mathf.Cos(angleRad);
			
			// open to the right side
			right = openDir;
			vertex = Converter.ToVector3(baseLane.points[i]) + right * openUnit / 2;
			vertices.Add(vertex);

			// open to the left side
			left = -openDir;
			openWidth = laneWidth * ((float)laneCount - 0.5f);
			vertex = Converter.ToVector3(baseLane.points[i]) + left * openWidth;	
			vertices.Add(vertex);
		}
		return vertices;
	}

	public List<int> BuildTriangles(int pointCnt)
	{
		List<int> triangles = new List<int>();
		for (int i = 0; i < pointCnt - 1; i++)
		{
			triangles.Add(2*i);
			triangles.Add(2*i + 1);
			triangles.Add(2*i + 2);

			triangles.Add(2*i + 1);
			triangles.Add(2*i + 3);
			triangles.Add(2*i + 2);
		}
		return triangles;
	}

	public void Create (EdgeData edgeData)
	{
		this.id = edgeData.id;
		data = edgeData;
		List<Vector3> vertices = BuildVertices(edgeData);
		List<int> triangles = BuildTriangles(edgeData.lanes[0].points.Count);

		Mesh mesh = new Mesh();
		mesh.SetVertices(vertices);
		mesh.SetTriangles(triangles, 0);
		mesh.RecalculateNormals();
		meshFilter.mesh = mesh;

		// Set material tiling
		// float length = 0f;
		// for (int i = 0; i < edgeData.lanes[0].points.Count - 1; i++)
		// {
		// 	Vector3 p1 = Converter.ToVector3(edgeData.lanes[0].points[i]);
		// 	Vector3 p2 = Converter.ToVector3(edgeData.lanes[0].points[i + 1]);
		// 	length += Vector3.Distance(p1, p2);
		// }
		// SetMaterialTiling(this.transform, length / 5f, (edgeData.lanes.Count * edgeData.lanes[0].width) / 5f);
	}
	public string GetId()
	{
		return id;
	}

	private void SetMaterialTiling(Transform lane, float x, float y) 
	{
		Material material = lane.GetComponentInChildren<Renderer>().material;
		material.mainTextureScale = new Vector2(x, y);
	}
}
