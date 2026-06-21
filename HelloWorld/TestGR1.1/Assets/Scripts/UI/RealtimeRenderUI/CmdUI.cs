using System;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine.Events;
using UnityEngine.UI;
using UnityEngine;
using TMPro;

public class CmdUI : MonoBehaviour
{
    [SerializeField] private Button pauseButton;
    [SerializeField] private PauseSO pauseSO;
    [SerializeField] private Button closeButton;
    [SerializeField] private NetworkSO networkSO;
    [SerializeField] private UnityEvent onSimulationEnd;


    private TcpClient cmdClient;
    private const int BUFFER_SIZE = 1024;
    private CancellationTokenSource _cts;

    private bool isPaused;

    void Start()
    {
        cmdClient = Network.CreateTcpClient(networkSO.Host, Constant.CMD_PORT);
        if (pauseButton != null)
            pauseButton.onClick.AddListener(OnPauseClicked);
        if (closeButton != null)
            closeButton.onClick.AddListener(OnCloseClicked);
        
        onSimulationEnd.AddListener(() =>
        {
            CursorManager.Instance.UnlockCursor();
        });

        _cts = new CancellationTokenSource();
        Task.Run(() => ListenForServerCommands(_cts.Token));
    }

    private void ListenForServerCommands(CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            try
            {
                if (cmdClient == null || !cmdClient.Connected) break;
                string msg = Network.ReadMessage(cmdClient, BUFFER_SIZE, Constant.END_MESSAGE);
                if (string.IsNullOrEmpty(msg)) break;
                if (msg == "Simulation end")
                    UnityMainThreadDispatcher.Instance()?.Enqueue(() => onSimulationEnd?.Invoke());
            }
            catch (Exception)
            {
                break;
            }
        }
    }

    private bool SendCommand(string command)
    {
        try
        {
            if (cmdClient == null || !cmdClient.Connected)
            {
                Network.CloseTcpClient(cmdClient);
                cmdClient = Network.CreateTcpClient(networkSO.Host, Constant.CMD_PORT);
            }

            bool ok = Network.SendMessage(cmdClient, command, BUFFER_SIZE, "<END>");
            Debug.Log($"Sent command: {command} | ok={ok}");
            return ok;
        }
        catch (SocketException e)
        {
            Debug.LogError($"Cmd socket error: {e.Message}");
            Network.CloseTcpClient(cmdClient);
            cmdClient = null;
            return false;
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Cmd error: {e.Message}");
            return false;
        }
    }

    private async Task<bool> SendCommandAsync(string command)
    {
        return await Task.Run(() => SendCommand(command));
    }

    private async void OnPauseClicked()
    {
        string cmd = isPaused ? "Resume" : "Pause";
        bool ok = await SendCommandAsync(cmd);
        if (ok)
        {
            isPaused = !isPaused;
        }
        if (isPaused){
            pauseButton.GetComponentInChildren<TMP_Text>().text = "Tiếp tục";
        } else {
            pauseButton.GetComponentInChildren<TMP_Text>().text = "Tạm dừng";
        }
        if (pauseSO != null)
        {
            pauseSO.isPaused = isPaused;
        }
    }

    private async void OnCloseClicked()
    {
        await SendCommandAsync("Simulation end");
        Application.Quit();
    }

    void OnDestroy()
    {
        _cts?.Cancel();
        Network.CloseTcpClient(cmdClient);
    }
}
