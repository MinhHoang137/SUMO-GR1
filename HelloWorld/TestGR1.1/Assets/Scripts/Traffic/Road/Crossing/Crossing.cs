using UnityEngine;

public class Crossing : MonoBehaviour
{
	private string id;
	private CrossingData data;
	public void Create(CrossingData data)
	{
		this.data = data;
		id = data.id;
		Vector3 direction = Vector3.zero;
		if (data.direction != null)
		{
			direction = new Vector3(data.direction.Value.x, 0, data.direction.Value.y).normalized;
		}
		Vector3 spread = new Vector3(direction.z, 0, -direction.x);
		float offset = data.width / 2;
		Vector3 position = new Vector3(data.start.x, 0, data.start.y) - offset * spread;
		transform.position = position;
		transform.forward = direction;
		transform.localScale = new Vector3(data.width, 1, data.length);
		Material material = GetComponentInChildren<Renderer>().material;
		if (material != null)
		{
			float textureScale = 2;
			material.mainTextureScale = new Vector2(data.width * textureScale, 1);
		}
	}
}
