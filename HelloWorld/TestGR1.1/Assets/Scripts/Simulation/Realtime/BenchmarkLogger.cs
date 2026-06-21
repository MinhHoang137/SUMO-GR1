using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

public class BenchmarkLogger : MonoBehaviour
{
    [SerializeField] private bool enableLogging = false;
    [SerializeField] private int flushEveryNSteps = 50;

    private StreamWriter _writer;
    private List<string> _buffer = new();
    private float _lastFps;
    private int _rowsSinceFlush;

    private double _sumFps;
    private double _sumLatency;
    private float _minFps = float.MaxValue;
    private int _count;

    private void Start()
    {
        if (!enableLogging) return;

        string dir = Path.Combine(Path.GetDirectoryName(Application.dataPath), "Benchmark");
        Directory.CreateDirectory(dir);
        string ts = DateTime.Now.ToString("yyyyMMdd_HHmmss");
        string path = Path.Combine(dir, $"bench_{ts}.csv");

        _writer = new StreamWriter(path, append: false, System.Text.Encoding.UTF8);
        _writer.WriteLine("Step,WallTimeMs,LatencyMs,FPS,CarCount,PedestrianCount");
        _writer.Flush();

        if (TrafficerManager.Instance != null)
            TrafficerManager.Instance.OnLatencyChanged += OnLatencyChanged;

        Debug.Log($"[BenchmarkLogger] Logging to {path}");
    }

    private void Update()
    {
        if (!enableLogging) return;
        _lastFps = Time.unscaledDeltaTime > 0f ? 1f / Time.unscaledDeltaTime : 0f;
    }

    private void OnLatencyChanged(object sender, TrafficerManager.LatencyEventArgs e)
    {
        if (_writer == null) return;

        var mgr = TrafficerManager.Instance;
        long wallMs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        _buffer.Add($"{mgr.CurrentStep},{wallMs},{e.LatencyMs},{_lastFps:F1},{mgr.CarCount},{mgr.PedestrianCount}");
        _rowsSinceFlush++;

        _sumFps += _lastFps;
        _sumLatency += e.LatencyMs;
        if (_lastFps < _minFps) _minFps = _lastFps;
        _count++;

        if (_rowsSinceFlush >= flushEveryNSteps)
            Flush();
    }

    private void Flush()
    {
        if (_writer == null || _buffer.Count == 0) return;
        foreach (var row in _buffer)
            _writer.WriteLine(row);
        _writer.Flush();
        _buffer.Clear();
        _rowsSinceFlush = 0;
    }

    private void OnDestroy()
    {
        if (TrafficerManager.Instance != null)
            TrafficerManager.Instance.OnLatencyChanged -= OnLatencyChanged;

        Flush();

        if (_writer != null && _count > 0)
        {
            _writer.WriteLine();
            _writer.WriteLine("# Tóm tắt");
            _writer.WriteLine($"# Tổng bước,{_count}");
            _writer.WriteLine($"# FPS TB,{(_sumFps / _count):F1}");
            _writer.WriteLine($"# FPS thấp nhất,{_minFps:F1}");
            _writer.WriteLine($"# Độ trễ TB (ms),{(_sumLatency / _count):F1}");
            _writer.Flush();
        }

        _writer?.Close();
        _writer = null;
    }
}
