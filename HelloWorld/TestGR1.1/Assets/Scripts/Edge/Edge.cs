using UnityEngine;

public class Edge : MonoBehaviour // edgeType_0
{
	private string id;
    [SerializeField] private Transform roadLanePrefab;
    [SerializeField] private Transform walkingLanePrefab;
    private float roadLaneWidth = 3.2f;
	private float roadOffset;
	private float walkingLaneWidth = 2f;
	private float walkingOffset;
    private EdgeData edgeData;
    public void Create(EdgeData edgeData)
    {
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
		Transform roadLane = Instantiate(roadLanePrefab, transform.position, Quaternion.identity);
		roadLane.transform.SetParent(transform);
		float roadLength = Vector3.Distance(new Vector3(edgeData.startRoadLane.x, 0, edgeData.startRoadLane.y), new Vector3(edgeData.endRoadLane.x, 0, edgeData.endRoadLane.y));
		float roadWidth = roadLaneWidth * edgeData.roadNum;
		roadLane.localScale = new Vector3(roadWidth, 1, roadLength);
		roadLane.transform.forward = new Vector3(edgeData.direction.x, 0, edgeData.direction.y);

		// Create walking lanes
		Transform walkingLane = Instantiate(walkingLanePrefab);
		walkingOffset = 0;
		walkingLane.position = transform.position + spread * (edgeData.roadNum * roadLaneWidth - walkingOffset);
		walkingLane.SetParent(transform);
		float walkingLength = Vector3.Distance(new Vector3(edgeData.startWalkingLane.x, 0, edgeData.startWalkingLane.y), new Vector3(edgeData.endWalkingLane.x, 0, edgeData.endWalkingLane.y));
		float walkingWidth = walkingLaneWidth * edgeData.walkingNum;
		walkingLane.localScale = new Vector3(walkingWidth, 1, walkingLength);
		walkingLane.forward = new Vector3(edgeData.direction.x, 0, edgeData.direction.y);
		SetMaterialTiling(walkingLane, walkingWidth, walkingLength);
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
