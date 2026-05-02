using UnityEngine;

public class Edge : Road // edgeType_0
{
	private string id;
    [SerializeField] private Transform walkingLanePrefab;
	[SerializeField] private RoadLane roadLanePrefab;
	private float roadLaneWidth = 3.2f;
	private float roadOffset;
	private float walkingLaneWidth = 2f;
	private float walkingOffset;
    private EdgeData edgeData;

	[Header("Decoration")]
	[Header("Tree settings")]
	[SerializeField] private Transform[] treePrefabs;
	[SerializeField] private float treeSpacing = 10f;
	
	[Header("House settings")]
	[SerializeField] private Transform[] housePrefabs;
	[SerializeField] private float houseMargin = 0.2f;
	
    public void Create(EdgeData edgeData)
    {
		//Debug.Log("Create Edge" + edgeData.id);
		if (id == null)
		{
			id = edgeData.id;
		}
		roadOffset = roadLaneWidth / 2;
		this.edgeData = edgeData;
		transform.position = new Vector3(edgeData.position.x, 0, edgeData.position.y);
        Vector3 spread = new Vector3(edgeData.direction.y, 0, -edgeData.direction.x);
        spread.Normalize(); 
		transform.position -= roadOffset * spread;

		float roadLength = Vector3.Distance(new Vector3(edgeData.startRoadLane.x, 0, edgeData.startRoadLane.y), new Vector3(edgeData.endRoadLane.x, 0, edgeData.endRoadLane.y));
		float roadWidth = roadLaneWidth * edgeData.roadNum;
		float walkingWidth = walkingLaneWidth * edgeData.walkingNum;
		Vector3 direction = new Vector3(edgeData.direction.x, 0, edgeData.direction.y).normalized;

		CreateRoadLanes(roadLength, roadWidth, direction);
		CreateWalkingLanes(spread, walkingWidth, direction);
		// CreateTrees(spread, direction, roadLength, roadWidth, walkingWidth);
		CreateHouses(spread, direction, roadLength, roadWidth, walkingWidth);
	}

	private void CreateRoadLanes(float roadLength, float roadWidth, Vector3 direction)
	{
		RoadLane roadLane = Instantiate(roadLanePrefab, transform.position, Quaternion.identity);
		roadLane.transform.SetParent(transform);
		roadLane.GetLane().localScale = new Vector3(roadWidth, 1, roadLength);
		roadLane.GetLaneMarking().localScale = new Vector3(roadLane.GetLaneMarking().localScale.x * roadLaneWidth, 1 , roadLength);
		roadLane.transform.forward = direction;
		float divider = 10;
		SetMaterialTiling(roadLane.GetLane(), edgeData.roadNum, roadLength / divider);
	}

	private void CreateWalkingLanes(Vector3 spread, float walkingWidth, Vector3 direction)
	{
		Transform walkingLane = Instantiate(walkingLanePrefab);
		walkingOffset = 0;
		walkingLane.position = transform.position + spread * (edgeData.roadNum * roadLaneWidth - walkingOffset);
		walkingLane.SetParent(transform);
		float walkingLength = 0;
		if (edgeData.startWalkingLane != null)
			walkingLength = Vector3.Distance(new Vector3(edgeData.startWalkingLane.Value.x, 0, edgeData.startWalkingLane.Value.y), new Vector3(edgeData.endWalkingLane.Value.x, 0, edgeData.endWalkingLane.Value.y));
		walkingLane.localScale = new Vector3(walkingWidth, 1, walkingLength);
		walkingLane.forward = direction;
		SetMaterialTiling(walkingLane, walkingWidth, walkingLength);
	}

	private void CreateTrees(Vector3 spread, Vector3 direction, float roadLength, float roadWidth, float walkingWidth)
	{
		float laneWidth = roadWidth + walkingWidth;
		float treeOffset = laneWidth + 1;
		float treeSpacing = this.treeSpacing;
		int treeCount = (int)(roadLength / treeSpacing);
		Vector3 startPos = new Vector3(edgeData.startRoadLane.x, 0, edgeData.startRoadLane.y);
		for (int i = 0; i < treeCount; i++)
		{
			Vector3 treePos = startPos + spread * treeOffset + direction * treeSpacing * i;
			Transform treePrefab = treePrefabs[Random.Range(0, treePrefabs.Length)];
			Transform tree = Instantiate(treePrefab, treePos, Quaternion.identity);
			tree.SetParent(transform);
		}
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

	private void CreateHouses(Vector3 spread, Vector3 direction, float roadLength, float roadWidth, float walkingWidth)
	{
		if (housePrefabs == null || housePrefabs.Length == 0) return;

		float laneWidth = roadWidth + walkingWidth;
		float spawnOffset = laneWidth; 

		Vector3 startPos = new Vector3(edgeData.startRoadLane.x, 0, edgeData.startRoadLane.y);
		float occupiedUpTo = 0f;
		
		int maxTries = 100;
		int currentTry = 0;

		while (occupiedUpTo < roadLength && currentTry < maxTries)
		{
			Transform housePrefab = housePrefabs[Random.Range(0, housePrefabs.Length)];
			BoxCollider col = housePrefab.GetComponent<BoxCollider>();
			if (col == null)
			{
				occupiedUpTo += 2f; 
				continue;
			}

			// Giả định góc xoay nhà hướng ra đường (-spread hoặc spread tuỳ prefab)
			Quaternion rotation = Quaternion.LookRotation(-spread);
			
			// Tính hình chiếu offset của tâm BoxCollider và hình chiếu kích thước BoxCollider lên bề mặt đường
			float offsetAlongRoad = Vector3.Dot(rotation * col.center, direction);
			float extentAlongRoad = Mathf.Abs(Vector3.Dot(rotation * new Vector3(col.size.x / 2f, 0, 0), direction)) 
			                      + Mathf.Abs(Vector3.Dot(rotation * new Vector3(0, 0, col.size.z / 2f), direction));
			
			// Tính khoảng cách từ tâm spawnPos lùi về mép gần nhất và tiến đến mép xa nhất
			float backwardsExtent = extentAlongRoad - offsetAlongRoad;
			float forwardsExtent = extentAlongRoad + offsetAlongRoad;

			// Tính toán currentLength (toạ độ sinh nhà) sao cho mép nhà gần nhất bắt đầu đúng từ vùng trống
			float currentLength = occupiedUpTo + backwardsExtent;
			Vector3 spawnPos = startPos + spread * spawnOffset + direction * currentLength;
			Vector3 boxCenter = spawnPos + rotation * col.center;

			float maxHouseBoundary = currentLength + forwardsExtent;

			// Nếu mép xa nhất của nhà tràn ra khỏi độ dài đường
			if (maxHouseBoundary > roadLength)
			{
				// Tràn về phía cuối con đường, coi như hết chỗ trống, kết thúc sinh nhà
				break;
			}

			Vector3 boxExtents = col.size / 2f + new Vector3(houseMargin, houseMargin, houseMargin); 
			
			// Kiểm tra OverlapBox (layer nào chứa các nhà đã sinh thì cần truyền vào, ở đây mặc định kiểm tra toàn bộ)
			Collider[] hits = Physics.OverlapBox(boxCenter, boxExtents, rotation);
			bool overlap = false;
			foreach (var hit in hits)
			{
				// Tránh BoxCollider mặt đất hoặc đường, có thể thêm kiểm tra tag như "House" cho an toàn hơn.
				if (hit.gameObject.CompareTag("Untagged") && hit.GetComponent<BoxCollider>() != null) // Thay đổi tag theo thực tế project
				{
					overlap = true;
					break;
				}
			}

			if (!overlap)
			{
				Instantiate(housePrefab, spawnPos, rotation, transform);
				// Cập nhật lại không gian bị chiếm dụng đến hết căn nhà hiện tại (+margin)
				occupiedUpTo = maxHouseBoundary + houseMargin;
			}
			else
			{
				occupiedUpTo += 1f; // Dịch lên 1 ít để tìm khoảng cách trống tiếp theo
			}
			currentTry++;
		}
	}
}
