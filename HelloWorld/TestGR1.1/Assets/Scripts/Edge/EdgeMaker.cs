using UnityEngine;

public class EdgeMaker : MonoBehaviour
{
    [SerializeField] private EdgeReader edgeReader;
	[SerializeField] private Edge edgePrefab;
	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
		edgeReader.OnReadComplete += EdgeReader_OnReadComplete;
	}

	private void EdgeReader_OnReadComplete(object sender, EdgeReader.OnReadCompleteEventArgs e)
	{
		Debug.Log("EdgeReader_OnReadComplete");
		foreach (EdgeData edgeData in e.edges)
		{
			Edge edge = Instantiate(edgePrefab);
			edge.Create(edgeData);
		}
	}
}
