using System;
using System.Collections.Generic;
using UnityEngine;

public class ManipulateAction : MonoBehaviour
{
    public static IEnumerator<WaitForSeconds> Delay(Action action, float delay)
	{
		yield return new WaitForSeconds(delay);
		action?.Invoke();
	}
	public static IEnumerator<WaitForSeconds> Wait(Func<bool> lockFunc, Action action)
	{
		while (lockFunc())
		{
			yield return new WaitForSeconds(0.1f);
		}
		action?.Invoke();
	}
}
