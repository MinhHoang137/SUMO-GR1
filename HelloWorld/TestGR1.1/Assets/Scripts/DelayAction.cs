using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class DelayAction : MonoBehaviour
{
    public static IEnumerator<WaitForSeconds> Delay(Action action, float delay)
	{
		yield return new WaitForSeconds(delay);
		action?.Invoke();
	}
}
