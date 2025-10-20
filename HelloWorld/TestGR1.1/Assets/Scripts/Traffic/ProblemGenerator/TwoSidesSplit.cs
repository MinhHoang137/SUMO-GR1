using System;
using System.Collections.Generic;
using NUnit.Framework;
using UnityEngine;

public class TwoSidesSplit : ISplitSide
{
    public Tuple<List<string>, List<string>> SplitSide(List<JunctionData> junctions)
    {
        List<string> sideA = new List<string>();
        List<string> sideB = new List<string>();
        float medianX = 0f;
        foreach (var junction in junctions)
        {
            medianX += junction.position[0];
        }
        medianX /= junctions.Count;
        foreach (var junction in junctions)
        {
            if (junction.position[0] < medianX)
            {
                sideA.Add(junction.id);
            }
            else
            {
                sideB.Add(junction.id);
            }
        }
        return Tuple.Create(sideA, sideB);
    }
}
