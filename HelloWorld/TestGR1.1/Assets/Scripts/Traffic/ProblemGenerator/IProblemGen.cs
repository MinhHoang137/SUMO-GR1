using System;
using System.Collections.Generic;

public interface IProblemGen
{
	/// <summary>
	/// Generate a traffic problem based on the provided split sides.
	/// </summary>
	/// <param name="junctions">A list of JunctionData objects representing the junctions in the traffic network.</param>
	/// <param name="numPairs">The number of start-end pairs to generate.</param>
	/// <returns>A tuple containing two lists of start and end points representing the journeys of vehicles or pedestrians.</returns>
	public Tuple<List<string>, List<string>> 
        Generate(List<JunctionData> junctions, int numPairs);
}