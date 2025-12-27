using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
public class Network
{
    public static TcpClient CreateTcpClient(string host, int port)
    {
        TcpClient client = new TcpClient();
        client.Connect(IPAddress.Parse(host), port);
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

    public static void CloseTcpClient(TcpClient client)
    {
        if (client != null)
        {
            client.Close();
        }
    }


}
