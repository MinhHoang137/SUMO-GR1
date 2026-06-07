using System.Collections.Generic;
using UnityEngine;

/*
	Sinh các khối nhà từ RoadDataSO.buildingDatas (chỉ có ở chế độ render OSM).
	Benchmark / custom-script không có building → danh sách rỗng, không tạo gì.
	Mỗi nhà: đặt GameObject tại trọng tâm footprint, dựng mesh extrude cục bộ.
*/
public class BuildingMaker : MonoBehaviour
{
	[SerializeField] private RoadDataSO roadData;
	[SerializeField] private Building buildingPrefab;
	// Mỗi nhà bốc 1 material ngẫu nhiên trong danh sách (ổn định theo id qua các lần chạy).
	// Để trống → giữ material mặc định của prefab.
	[SerializeField] private Material[] buildingMaterials;

	private readonly Dictionary<string, Building> buildingMap = new Dictionary<string, Building>();
	private bool created = false;

	private void Start()
	{
		// roadData.buildingDatas có thể null (mode khác) → chờ tới khi có dữ liệu;
		// nếu là benchmark thì không bao giờ có và coroutine chỉ poll nhẹ, không tạo gì.
		StartCoroutine(ManipulateAction.Wait(
			() => !created && (roadData.buildingDatas == null || roadData.buildingDatas.Count == 0),
			() => CreateBuildings(roadData.buildingDatas)
		));
	}

	private void CreateBuildings(List<BuildingData> buildings)
	{
		if (created || buildings == null) return;
		created = true;
		foreach (var data in buildings)
		{
			if (data == null || data.vertices == null || data.vertices.Count < 3) continue;
			if (data.id != null && buildingMap.ContainsKey(data.id)) continue;
			Building b = CreateBuilding(data);
			if (b != null && data.id != null) buildingMap[data.id] = b;
		}
	}

	private Building CreateBuilding(BuildingData data)
	{
		// Trọng tâm footprint (world) làm gốc đối tượng → đỉnh cục bộ = world - centroid.
		Vector3 centroid = Vector3.zero;
		List<Vector3> worldVerts = new List<Vector3>(data.vertices.Count);
		foreach (var v in data.vertices)
		{
			Vector3 w = Converter.ToVector3(v);
			worldVerts.Add(w);
			centroid += w;
		}
		centroid /= worldVerts.Count;

		Building building = Instantiate(buildingPrefab, centroid, Quaternion.identity);
		building.data = data;
		building.baseVertices = new List<Vector3>(worldVerts.Count);
		foreach (var w in worldVerts)
		{
			building.baseVertices.Add(w - centroid);
		}
		building.Create(building.baseVertices.ToArray(), data.height, data.id);
		building.SetMaterial(PickMaterial(data.id));
		building.transform.SetParent(transform);
		return building;
	}

	// Chọn material ổn định theo id (cùng nhà luôn ra cùng material, không nhấp nháy khi
	// reconnect). Hash id thay vì Random.Range để tái lập được.
	private Material PickMaterial(string id)
	{
		if (buildingMaterials == null || buildingMaterials.Length == 0) return null;
		int hash = string.IsNullOrEmpty(id) ? 0 : id.GetHashCode();
		int idx = (hash & 0x7fffffff) % buildingMaterials.Length;
		return buildingMaterials[idx];
	}
}
