using UnityEngine;

public class Crossing : MonoBehaviour
{
	// Số lần lặp pattern texture mỗi mét chiều rộng. Trước đây set qua material.mainTextureScale
	// (per-instance) — không batch được. Giờ bake vào mesh UV → share material → batch OK.
	private const float TEXTURE_REPEATS_PER_METER = 2f;

	private string id;
	private CrossingData data;
	public void Create(CrossingData data)
	{
		this.data = data;
		id = data.id;
		Vector3 direction = Vector3.zero;
		if (data.direction != null)
		{
			direction = Converter.ToVector3(data.direction.Value).normalized;
		}
		Vector3 spread = new Vector3(direction.z, 0, -direction.x);
		float offset = data.width / 2;
		Vector3 position = Converter.ToVector3(data.start) - offset * spread;
		transform.position = position;
		transform.forward = direction;
		transform.localScale = new Vector3(data.width, 1, data.length);

		// Bake texture scale vào UV thay vì modify material instance → mọi Crossing share
		// sharedMaterial của prefab → DrawCallsReducer combine được trong cùng draw call.
		MeshFilter mf = GetComponentInChildren<MeshFilter>();
		if (mf != null && mf.sharedMesh != null)
		{
			Mesh src = mf.sharedMesh;
			Vector2[] srcUv = src.uv;
			if (srcUv != null && srcUv.Length > 0)
			{
				float uScale = data.width * TEXTURE_REPEATS_PER_METER;
				Vector2[] uv = new Vector2[srcUv.Length];
				for (int i = 0; i < srcUv.Length; i++)
				{
					uv[i] = new Vector2(srcUv[i].x * uScale, srcUv[i].y);
				}
				// Clone mesh để không modify shared prefab asset.
				Mesh m = Instantiate(src);
				m.uv = uv;
				mf.mesh = m;
			}
		}
	}
}
