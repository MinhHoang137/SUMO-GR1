using UnityEngine;

public class Converter 
{
    public static Vector3 ToVector3(float[] floats, float y = 0f)
    {
        if (floats == null || floats.Length < 2)
            return Vector3.zero;

        return new Vector3(floats[0], y, floats[1]);
    }
}
