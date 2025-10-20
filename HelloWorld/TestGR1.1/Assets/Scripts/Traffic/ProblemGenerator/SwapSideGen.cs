using System;
using System.Collections.Generic;

public class SwapSideGen : IProblemGen
{
    public Tuple<List<string>, List<string>> Generate(List<JunctionData> junctions, int numPairs)
    {
        Tuple<List<string>, List<string>> splitSides = new TwoSidesSplit().SplitSide(junctions);
        List<string> copyLeft = new(splitSides.Item1);
        List<string> copyRight = new(splitSides.Item2);
        List<string> startPoints = new();
        List<string> endPoints = new();
        Random rand = new();
        int genNumPairs = Math.Min(numPairs, Math.Min(copyLeft.Count, copyRight.Count));
        if (genNumPairs <= 0)
        {
            return Tuple.Create(startPoints, endPoints);
        }
        for (int i = 0; i < genNumPairs; i++)
        {
            if (i % 2 == 0)
            {
                int startIndex = rand.Next(copyLeft.Count);
                int endIndex = rand.Next(copyRight.Count);
                startPoints.Add(copyLeft[startIndex]);
                endPoints.Add(copyRight[endIndex]);
                copyLeft.RemoveAt(startIndex);
                copyRight.RemoveAt(endIndex);
            }
            else
            {
                int startIndex = rand.Next(copyRight.Count);
                int endIndex = rand.Next(copyLeft.Count);
                startPoints.Add(copyRight[startIndex]);
                endPoints.Add(copyLeft[endIndex]);
                copyRight.RemoveAt(startIndex);
                copyLeft.RemoveAt(endIndex);
            }
        }
        return Tuple.Create(startPoints, endPoints);
    }
}
