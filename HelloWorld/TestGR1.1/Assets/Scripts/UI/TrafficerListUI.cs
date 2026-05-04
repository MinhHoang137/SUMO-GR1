using UnityEngine;
using UnityEngine.UI;
using System;
using System.Collections.Generic;

public class TrafficerListUI : MonoBehaviour
{
    [SerializeField] private Button showHideToggle;
    [SerializeField] private GameObject scrollView;
    [SerializeField] private RectTransform itemHolder;
    [SerializeField] private TrafficerButton itemPrefab;
	private float unit = 35;
    private int itemCount = 0;

    private Dictionary<string, TrafficerButton> trafficerButtonDict = new();

	// Start is called once before the first execution of Update after the MonoBehaviour is created
	void Start()
    {
        showHideToggle.onClick.AddListener(() => {
            scrollView.SetActive(!scrollView.activeSelf);
        });
		itemHolder.sizeDelta = new Vector2(itemHolder.sizeDelta.x, unit * itemCount);
        TrafficerManager.Instance.OnAddTrafficer += (sender, e) =>
		{
			AddItem(e.Trafficer);
		};
		TrafficerManager.Instance.OnRemoveTrafficer += (sender, e) =>
		{
			RemoveItem(e.Trafficer.GetId());
		};
	}
    private void AddItem(Trafficer trafficer)
	{
		TrafficerButton button = Instantiate(itemPrefab, itemHolder);
		if (trafficer.TryGetComponent<UnityVehicle>(out UnityVehicle vehicle))
		{
			button.transform.SetAsFirstSibling();
		}
		button.SetTrafficerId(trafficer.GetId());
		itemCount++;
		itemHolder.sizeDelta = new Vector2(itemHolder.sizeDelta.x, unit * itemCount);
		trafficerButtonDict.Add(trafficer.GetId(), button);
	}
	private void RemoveItem(string trafficerId)
	{
		if (trafficerButtonDict.TryGetValue(trafficerId, out TrafficerButton button))
		{ 
			trafficerButtonDict.Remove(trafficerId);
			itemCount--;
			Destroy(button.gameObject);
			itemHolder.sizeDelta = new Vector2(itemHolder.sizeDelta.x, unit * itemCount);
		}
	}
}
