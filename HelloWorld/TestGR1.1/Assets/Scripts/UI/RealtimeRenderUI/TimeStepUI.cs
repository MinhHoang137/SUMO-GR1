using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using Unity.VisualScripting;
using UnityEngine;

public class TimeStepUI : MonoBehaviour
{
    [SerializeField] private ValueUI timeStepValueUI;
    [SerializeField] private SpeedMultiplierUI speedMultiplierUI;
    private int currentTimeStep = 1000;
    private bool isEditable = false;
    [SerializeField] private NetworkSO networkSO;
    private CancellationTokenSource _debounceCts;

    // time_step hiện tại (giây) — dùng để bù tốc độ xe client mirror trước khi upload (xem UnityVehicle.GetUnityVehicleData).
    public static float CurrentTimeStepSeconds { get; private set; } = 1f;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        timeStepValueUI.Create((value) =>
        {
            if (value < 1f)
            {
                value = 1f;
            }

            DebounceSendParameters((int)value);

            if (isEditable)
            {
                float ratio = value / currentTimeStep;
                speedMultiplierUI.ScaleValueInversely(ratio);
                currentTimeStep = (int)value;
                CurrentTimeStepSeconds = currentTimeStep / 1000f;
            }
        });
        isEditable = true;
        currentTimeStep = (int)timeStepValueUI.GetValue();
        CurrentTimeStepSeconds = currentTimeStep / 1000f;
        SendParameters(currentTimeStep);
    }

    private async void DebounceSendParameters(int timeStep)
    {
        _debounceCts?.Cancel();
        _debounceCts = new CancellationTokenSource();
        var token = _debounceCts.Token;

        try
        {
            await Task.Delay(200, token);
            if (token.IsCancellationRequested) return;

            await Task.Run(() =>
            {
                bool result = SendParameters(timeStep);
                if (!result)
                {
                    Debug.LogError("Failed to send time step parameters to the server.");
                }
            }, token);
        }
        catch (TaskCanceledException)
        {
            // Ignore
        }
    }

    private bool SendParameters(int timeStep)
    {
        Parameters parameters = new Parameters();
        parameters.timeStep = timeStep;
        TcpClient paramClient = Network.CreateTcpClient(networkSO.Host, Constant.CMD_PORT);
        bool result = Network.SendData(paramClient, parameters, Constant.BUFFER_SIZE);
        return result;
    }
    private void OnDestroy()
    {
        timeStepValueUI.Destroy();
    }
}
