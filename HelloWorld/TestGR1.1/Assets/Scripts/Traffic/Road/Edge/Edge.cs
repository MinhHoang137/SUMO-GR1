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

	public string GetId() => id;
	public EdgeData GetData() => data;

	public void Create(EdgeData edgeData)
	{
		if (edgeData == null || edgeData.lanes == null || edgeData.lanes.Count == 0)
		{
			return;
		}

		id = edgeData.id;
		data = edgeData;

		for (int i = 0; i < edgeData.lanes.Count; i++)
		{
			BuildLane(edgeData.lanes[i], i);
		}
	}

	private void BuildLane(Lane lane, int index)
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
		mesh.SetVertices(BuildLaneVertices(lane));
		mesh.SetTriangles(BuildLaneTriangles(lane.points.Count), 0);
		mesh.RecalculateNormals();
		mf.mesh = mesh;
	}

	private List<Vector3> BuildLaneVertices(Lane lane)
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
				right = Vector3.Cross(dir.normalized, -Vector3.up);
			}
			else if (i == pointCnt - 1)
			{
				Vector3 dir = pt - Converter.ToVector3(lane.points[i - 1]);
				right = Vector3.Cross(dir.normalized, -Vector3.up);
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

			vertices.Add(pt + right * dist);
			vertices.Add(pt - right * dist);
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
