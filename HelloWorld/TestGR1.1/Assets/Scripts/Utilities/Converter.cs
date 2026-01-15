using UnityEngine;

public class Converter 
{
    public static Vector3 ToVector3(float[] floats)
    {
        if (floats == null || floats.Length < 2)
            return Vector3.zero;

        float y = floats.Length >= 3 ? floats[2] : 0f;
        return new Vector3(floats[0], y, floats[1]);
    }

    public static float[] ToFloatArray(Vector3 vector)
    {
        return new float[] { vector.x, vector.z, vector.y };
    }

    /// <summary>
    /// Chuyển đổi từ tọa độ trong SUMO sang Vector3 phù hợp với không gian trong Unity
    /// </summary>
    /// <param name="coord"></param>
    /// <returns></returns>
    public static Vector3 ToVector3(Coordinate coord)
    {
        return new Vector3(coord.x, coord.z, coord.y);
    }
}
