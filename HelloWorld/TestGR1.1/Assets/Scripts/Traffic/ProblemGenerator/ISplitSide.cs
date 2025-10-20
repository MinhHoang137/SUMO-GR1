using System;
using System.Collections.Generic;
using UnityEngine;

public interface ISplitSide
{
    /// <summary>
    /// split a list of junctions into two sides.
    /// </summary>
    /// <param name="junctions">The list of junctions to be split.</param>
    /// <returns>A tuple containing two lists of junction IDs representing the two sides.</returns>
    public Tuple<List<string>, List<string>> 
        SplitSide(List<JunctionData> junctions);
}
