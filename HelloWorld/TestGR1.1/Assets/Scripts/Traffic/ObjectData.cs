using UnityEngine;
using System;
using Newtonsoft.Json;

[Serializable]
public class ObjectData
{
    [JsonProperty("t")]
    [SerializeField] protected string type;
	public string Type => type;
}
