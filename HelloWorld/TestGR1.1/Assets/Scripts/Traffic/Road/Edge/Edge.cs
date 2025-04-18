using UnityEngine;

public class Edge : Road // edgeType_0
{
	private string id;
    [SerializeField] private Transform walkingLanePrefab;
	[SerializeField] private Transform[] treePrefabs;
	[SerializeField] private RoadLane roadLanePrefab;
	private float roadLaneWidth = 3.2f;
	private float roadOffset;
	private float walkingLaneWidth = 2f;
	private float walkingOffset;
    private EdgeData edgeData;
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

		// Create road lanes
		RoadLane roadLane = Instantiate(roadLanePrefab, transform.position, Quaternion.identity);
		roadLane.transform.SetParent(transform);
		float roadLength = Vector3.Distance(new Vector3(edgeData.startRoadLane.x, 0, edgeData.startRoadLane.y), new Vector3(edgeData.endRoadLane.x, 0, edgeData.endRoadLane.y));
		float roadWidth = roadLaneWidth * edgeData.roadNum;
		roadLane.GetLane().localScale = new Vector3(roadWidth, 1, roadLength);
		roadLane.GetLaneMarking().localScale = new Vector3(roadLane.GetLaneMarking().localScale.x * roadLaneWidth, 1 , roadLength);
		Vector3 direction = new Vector3(edgeData.direction.x, 0, edgeData.direction.y).normalized;
		roadLane.transform.forward = direction;
		float divider = 10;
		SetMaterialTiling(roadLane.GetLane(), edgeData.roadNum, roadLength/divider);

		// Create walking lanes
		Transform walkingLane = Instantiate(walkingLanePrefab);
		walkingOffset = 0;
		walkingLane.position = transform.position + spread * (edgeData.roadNum * roadLaneWidth - walkingOffset);
		walkingLane.SetParent(transform);
		float walkingLength = 0;
		if (edgeData.startWalkingLane != null)
		walkingLength = Vector3.Distance(new Vector3(edgeData.startWalkingLane.x, 0, edgeData.startWalkingLane.y), new Vector3(edgeData.endWalkingLane.x, 0, edgeData.endWalkingLane.y));
		float walkingWidth = walkingLaneWidth * edgeData.walkingNum;
		walkingLane.localScale = new Vector3(walkingWidth, 1, walkingLength);
		walkingLane.forward = direction;
		SetMaterialTiling(walkingLane, walkingWidth, walkingLength);

		// Create trees
		float laneWidth = roadWidth + walkingWidth;
		float treeOffset = laneWidth + 1;
		float treeSpacing = 10;
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
}
