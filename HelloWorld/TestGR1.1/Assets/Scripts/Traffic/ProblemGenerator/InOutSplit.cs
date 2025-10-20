using System;
using System.Collections.Generic;
using UnityEngine;

public class InOutSplit : ISplitSide
{
    public Tuple<List<string>, List<string>> SplitSide(List<JunctionData> junctions)
    {
        List<string> inside = new List<string>();
        List<string> outside = new List<string>();

        float[] center = new float[2] { 0f, 0f };
        foreach (var junction in junctions)
        {
            center[0] += junction.position[0];
            center[1] += junction.position[1];
        }
        center[0] /= junctions.Count;
        center[1] /= junctions.Count;

        float medianRadius = 0f;
        foreach (var junction in junctions)
        {
            float dx = junction.position[0] - center[0];
            float dy = junction.position[1] - center[1];
            medianRadius += Mathf.Sqrt(dx * dx + dy * dy);
        }
        medianRadius /= junctions.Count;

        foreach (var junction in junctions)
        {
            float dx = junction.position[0] - center[0];
            float dy = junction.position[1] - center[1];
            float distance = Mathf.Sqrt(dx * dx + dy * dy);
            if (distance < medianRadius)
            {
                inside.Add(junction.id);
            }
            else
            {
                outside.Add(junction.id);
            }
        }

        return Tuple.Create(inside, outside);
    }
}