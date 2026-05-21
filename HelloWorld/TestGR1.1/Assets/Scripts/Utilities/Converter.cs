using UnityEngine;

public class Converter
{
    /// SUMO (x, y[, z_up]) → Unity (x, y_up, z). Dùng floats[2] cho trục đứng nếu có; ngược lại fallback `y`.
    public static Vector3 ToVector3(float[] floats, float y = 0f)
    {
        if (floats == null || floats.Length < 2)
            return Vector3.zero;

        float yVal = floats.Length >= 3 ? floats[2] : y;
        return new Vector3(floats[0], yVal, floats[1]);
    }

    /// SUMO (x, y, z) với z là trục đứng → Unity (x, y, z) với y là trục đứng.
    public static Vector3 ToVector3(Coordinate coord)
    {
        return new Vector3(coord.x, coord.z, coord.y);
    }

    public static Vector3 ToVector3(JunctionData.Vertex vertex)
    {
        return new Vector3(vertex.x, vertex.z, vertex.y);
    }

    public static float[] ToFloatArray(Vector3 vector)
    {
        return new float[] { vector.x, vector.z, vector.y };
    }
}
