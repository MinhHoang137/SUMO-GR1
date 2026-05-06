using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
public class Network
{
    private static Dictionary<string, TcpClient> _connectedClients = new Dictionary<string, TcpClient>();

    public static TcpClient CreateTcpClient(string host, int port)
    {
        string key = $"{host}:{port}";
        if (_connectedClients.TryGetValue(key, out TcpClient existingClient))
        {
            if (existingClient.Connected)
            {
                return existingClient;
            }
            _connectedClients.Remove(key);
        }

        TcpClient client = new TcpClient();
        client.Connect(IPAddress.Parse(host), port);
        _connectedClients[key] = client;
        return client;
    }

    public static string ReadMessage(TcpClient client, int bufferSize, string endMarker)
    {
        NetworkStream stream = client.GetStream();
        byte[] buffer = new byte[bufferSize];
        StringBuilder fullMessage = new StringBuilder();
        int bytesRead;

        while ((bytesRead = stream.Read(buffer, 0, buffer.Length)) > 0)
        {
            string chunk = Encoding.UTF8.GetString(buffer, 0, bytesRead);
            fullMessage.Append(chunk);
            if (fullMessage.ToString().Contains(endMarker))
            {
                break;
            }
        }
        
        string message = fullMessage.ToString();
        int endIndex = message.IndexOf(endMarker);
        if (endIndex >= 0)
        {
            message = message.Substring(0, endIndex);
        }

        if (client.Client.RemoteEndPoint != null)
        {
            // Debug.Log($"[Network] Đã nhận gói tin từ {client.Client.RemoteEndPoint} - Kích thước: {Encoding.UTF8.GetByteCount(message)} bytes");
        }

        return message;
    }

    public static bool SendMessage(TcpClient client, string message, int bufferSize, string endMarker)
    {
        if (client == null || !client.Connected)
        {
            return false;
        }

        NetworkStream stream = client.GetStream();
        string fullMessage = message + endMarker;
        byte[] messageBytes = Encoding.UTF8.GetBytes(fullMessage);

        int totalBytesSent = 0;
        while (totalBytesSent < messageBytes.Length)
        {
            int bytesToSend = Math.Min(bufferSize, messageBytes.Length - totalBytesSent);
            stream.Write(messageBytes, totalBytesSent, bytesToSend);
            totalBytesSent += bytesToSend;
        }

        return true;
    }

    public static bool SendData<T>(TcpClient client, T data, int bufferSize) where T : class
    {
        if (client == null || !client.Connected)
        {
            return false;
        }

        NetworkStream stream = client.GetStream();
        string jsonData = JsonConvert.SerializeObject(data);
        return SendMessage(client, jsonData, bufferSize, "<END>");
    }

    public static void CloseTcpClient(TcpClient client)
    {
        if (client != null)
        {
            string keyToRemove = null;
            foreach (var kvp in _connectedClients)
            {
                if (kvp.Value == client)
                {
                    keyToRemove = kvp.Key;
                    break;
                }
            }

            if (keyToRemove != null)
            {
                _connectedClients.Remove(keyToRemove);
            }

            client.Close();
        }
    }


}
