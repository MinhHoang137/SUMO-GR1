using UnityEngine;
using System;

[Serializable]
public class ObjectData
{
    [SerializeField] protected string type;
	public string Type => type;
}
