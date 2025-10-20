using System;
using System.Collections.Generic;

public class CrossSideGen : IProblemGen
{
	public Tuple<List<string>, List<string>> Generate(List<JunctionData> junctions, int numPairs)
    {
        Tuple<List<string>, List<string>> splitSides = new TwoSidesSplit().SplitSide(junctions);
		List<string> copyStart = new(splitSides.Item1);
        List<string> copyEnd = new(splitSides.Item2);
        List<string> startPoints = new();
        List<string> endPoints = new();
        Random rand = new();

        int genNumPairs = Math.Min(numPairs, Math.Min(copyStart.Count, copyEnd.Count));
        if (genNumPairs < 0)
        {
            return Tuple.Create(startPoints, endPoints);
        }

        for (int i = 0; i < genNumPairs; i++)
        {
            int startIndex = rand.Next(copyStart.Count);
            int endIndex = rand.Next(copyEnd.Count);
            startPoints.Add(copyStart[startIndex]);
            endPoints.Add(copyEnd[endIndex]);
            copyStart.RemoveAt(startIndex);
            copyEnd.RemoveAt(endIndex);
        }
        return Tuple.Create(startPoints, endPoints);
    }
}