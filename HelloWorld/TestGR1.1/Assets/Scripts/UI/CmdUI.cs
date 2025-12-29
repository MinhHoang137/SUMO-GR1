using System.Net.Sockets;
using System.Threading.Tasks;
using UnityEngine.UI;
using UnityEngine;
using TMPro;

public class CmdUI : MonoBehaviour
{
    [SerializeField] private Button pauseButton;
    [SerializeField] private Button closeButton;

    private TcpClient cmdClient;
    private const string SERVER_IP = "127.0.0.1";
    private const int PORT = 5054;
    private const int BUFFER_SIZE = 1024;

    private bool isPaused;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        cmdClient = Network.CreateTcpClient(SERVER_IP, PORT);
        if (pauseButton != null)
        {
            pauseButton.onClick.AddListener(OnPauseClicked);
        }

        if (closeButton != null)
        {
            closeButton.onClick.AddListener(OnCloseClicked);
        }
    }

    private bool SendCommand(string command)
    {
        try
        {
            if (cmdClient == null || !cmdClient.Connected)
            {
                Network.CloseTcpClient(cmdClient);
                cmdClient = Network.CreateTcpClient(SERVER_IP, PORT);
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
    }

    private async void OnCloseClicked()
    {
        await SendCommandAsync("Simulation end");
        Application.Quit();
    }

    void OnDestroy()
    {
        Network.CloseTcpClient(cmdClient);
    }
}
