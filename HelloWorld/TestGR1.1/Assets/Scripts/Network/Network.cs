using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
public class Network
{
    private static Dictionary<string, TcpClient> _connectedClients = new Dictionary<string, TcpClient>();

    // Tiền tố đánh dấu payload đã nén (raw-deflate + base64) từ server — khớp GZ_PREFIX ở network.py.
    private const string GZ_PREFIX = "GZ:";

    // Nếu message có tiền tố GZ: → base64-decode rồi giải nén raw-deflate về JSON gốc.
    // Không có tiền tố → trả nguyên (JSON thường — tương thích ngược / khi tắt nén ở server).
    public static string MaybeDecompress(string message)
    {
        if (string.IsNullOrEmpty(message) || !message.StartsWith(GZ_PREFIX, StringComparison.Ordinal))
        {
            return message;
        }
        byte[] compressed = Convert.FromBase64String(message.Substring(GZ_PREFIX.Length));
        using (var input = new MemoryStream(compressed))
        using (var deflate = new DeflateStream(input, CompressionMode.Decompress))
        using (var reader = new StreamReader(deflate, Encoding.UTF8))
        {
            return reader.ReadToEnd();
        }
    }

    // Buffer nhận bền theo từng kết nối — giữ phần dư sau END_MARKER (giống _recv_buffers ở network.py)
    // để không rớt message khi TCP gộp nhiều gói vào một lần đọc.
    private class RecvBuffer
    {
        public byte[] data = new byte[131072];
        public int length;   // số byte hợp lệ đang giữ trong data
        public int scanPos;  // đã quét END_MARKER tới đâu (tránh quét lại từ đầu — O(n) thay vì O(n²))
    }
    private static readonly Dictionary<TcpClient, RecvBuffer> _recvBuffers = new Dictionary<TcpClient, RecvBuffer>();
    private static readonly object _recvLock = new object();

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
        client.NoDelay = true; // tắt Nagle: stream realtime nhỏ, nhịp ~50ms → cần độ trễ thấp, tránh gộp/giữ gói.
        _connectedClients[key] = client;
        return client;
    }

    // Đọc đúng một message kết thúc bằng endMarker từ luồng TCP.
    // - Giữ buffer bền per-connection → phần dư sau marker dành cho lần đọc kế (không rớt frame khi gói dính nhau).
    // - Quét marker ở mức byte (endMarker toàn ASCII <0x80 nên không đụng chuỗi UTF-8 đa byte) và quét
    //   incremental từ scanPos → tổng chi phí O(n) thay vì O(n²) như bản cũ (ToString().Contains mỗi chunk).
    // Trả về "" khi kết nối đã đóng.
    public static string ReadMessage(TcpClient client, int bufferSize, string endMarker)
    {
        byte[] marker = Encoding.ASCII.GetBytes(endMarker);

        RecvBuffer cb;
        lock (_recvLock)
        {
            if (!_recvBuffers.TryGetValue(client, out cb))
            {
                cb = new RecvBuffer();
                _recvBuffers[client] = cb;
            }
        }

        NetworkStream stream = client.GetStream();
        while (true)
        {
            int idx = IndexOf(cb.data, cb.length, marker, cb.scanPos);
            if (idx >= 0)
            {
                string message = Encoding.UTF8.GetString(cb.data, 0, idx);
                // Dồn phần dư (byte sau marker) về đầu buffer cho lần đọc kế.
                int remStart = idx + marker.Length;
                int remLen = cb.length - remStart;
                if (remLen > 0)
                {
                    Buffer.BlockCopy(cb.data, remStart, cb.data, 0, remLen);
                }
                cb.length = remLen;
                cb.scanPos = 0;
                return message;
            }

            // Chưa thấy marker: lần sau quét tiếp từ gần cuối (lùi marker.Length-1 để bắt marker bị cắt ngang gói).
            cb.scanPos = Math.Max(0, cb.length - (marker.Length - 1));

            // Bảo đảm còn chỗ trống để đọc (hỗ trợ message lớn hơn bufferSize — vd road data).
            if (cb.data.Length - cb.length < bufferSize)
            {
                Array.Resize(ref cb.data, cb.length + bufferSize);
            }

            int bytesRead = stream.Read(cb.data, cb.length, cb.data.Length - cb.length);
            if (bytesRead <= 0)
            {
                return string.Empty; // kết nối đóng
            }
            cb.length += bytesRead;
        }
    }

    // Tìm pattern trong buf[start..len), trả về chỉ số bắt đầu hoặc -1.
    private static int IndexOf(byte[] buf, int len, byte[] pattern, int start)
    {
        int end = len - pattern.Length;
        for (int i = Math.Max(0, start); i <= end; i++)
        {
            bool match = true;
            for (int j = 0; j < pattern.Length; j++)
            {
                if (buf[i + j] != pattern[j]) { match = false; break; }
            }
            if (match) return i;
        }
        return -1;
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

            lock (_recvLock)
            {
                _recvBuffers.Remove(client);
            }

            client.Close();
        }
    }


}
