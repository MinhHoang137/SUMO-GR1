using UnityEngine;

public class Crossing : MonoBehaviour
{
	private string id;
	private CrossingData data;
	public void Create(CrossingData data)
	{
		this.data = data;
		id = data.id;
		Vector3 start = Converter.ToVector3(data.start);
		Vector3 end = Converter.ToVector3(data.end);

		// Use provided direction if available; otherwise infer from endpoints.
		Vector3 direction = (end - start);
		if (data.direction != null)
		{
			direction = Converter.ToVector3(data.direction.Value);
		}
		if (direction.sqrMagnitude < 1e-6f)
		{
			direction = Vector3.forward;
		}

		// Keep crossing orientation flat on the ground plane (XZ) for stability.
		Vector3 planarDir = new Vector3(direction.x, 0f, direction.z).normalized;
		Vector3 spread = new Vector3(planarDir.z, 0f, -planarDir.x);
		float offset = data.width / 2f;

		// Place at the start elevation (SUMO z -> Unity y). If endpoints differ, midpoint height is a reasonable fallback.
		float y = (start.y + end.y) * 0.5f;
		Vector3 position = new Vector3(start.x, y, start.z) - offset * spread;
		transform.position = position;
		transform.forward = planarDir;
		transform.localScale = new Vector3(data.width, 1, data.length);
		Material material = GetComponentInChildren<Renderer>().material;
		if (material != null)
		{
			float textureScale = 2;
			material.mainTextureScale = new Vector2(data.width * textureScale, 1);
		}
	}
}
