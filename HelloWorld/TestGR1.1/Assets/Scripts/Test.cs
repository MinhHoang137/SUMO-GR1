using System;
using System.Collections.Generic;
using UnityEngine;

public class Test : MonoBehaviour
{
    [SerializeField] private RoadDataSO roadData;
    private float medianX;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        Tuple<List<string>, List<string>> splitSides = new SwapSideGen().Generate(roadData.junctionDatas, 5);
        Debug.Log("Start Points: " + string.Join(", ", splitSides.Item1));
        Debug.Log("End Points: " + string.Join(", ", splitSides.Item2));
        medianX = GetMedianX(roadData.junctionDatas);
    }

    // Update is called once per frame
    void Update()
    {
        Vector3 startPos = new Vector3(medianX, 0f, 0f);
        Vector3 dir = new Vector3(0, 0, 1f);
        Debug.DrawRay(startPos, dir * 100f, Color.red);
    }

    private void GenerateLine(List<JunctionData> junctions)
    {
        LineRenderer lineRenderer = GetComponent<LineRenderer>();
        lineRenderer.positionCount = 1;
        float medianX = 0f;
        foreach (var junction in junctions)
        {
            medianX += junction.position[0];
        }
        medianX /= junctions.Count;
        lineRenderer.SetPosition(0, new Vector3(medianX, transform.position.y, 0f));
    }
    private float GetMedianX(List<JunctionData> junctions)
    {
        float medianX = 0f;
        foreach (var junction in junctions)
        {
            medianX += junction.position[0];
        }
        medianX /= junctions.Count;
        return medianX;
    }
}
