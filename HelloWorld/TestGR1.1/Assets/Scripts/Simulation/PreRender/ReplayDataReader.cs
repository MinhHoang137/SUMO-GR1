using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using UnityEngine;

public class ReplayDataReader
{
    private string filePath;
    private List<long> stepOffsets = new List<long>();
    private List<int> stepLengths = new List<int>();
    public int TotalSteps { get; private set; }

    private const int MAX_CHUNK_BYTES = 10 * 1024 * 1024; // 10MB
    
    private class ChunkData
    {
        public int startStep;
        public int endStep;
        public List<TrafficDataList> frames = new List<TrafficDataList>();
    }

    private ChunkData activeChunk = null;
    private ChunkData prefetchingChunk = null;
    private bool isPrefetching = false;
    private int prefetchTargetStart = -1;

    public ReplayDataReader(string filePath)
    {
        this.filePath = filePath;
        BuildIndex();
    }

    private void BuildIndex()
    {
        stepOffsets.Clear();
        stepLengths.Clear();

        if (!File.Exists(filePath))
        {
            Debug.LogError($"[ReplayDataReader] JSON File not found: {filePath}");
            return;
        }

        using (FileStream fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            byte[] buffer = new byte[1024 * 1024]; // 1MB buffer for fast scanning
            int bytesRead;
            long absolutePosition = 0;
            
            long currentItemStart = -1;
            bool insideItem = false;
            
            while ((bytesRead = fs.Read(buffer, 0, buffer.Length)) > 0)
            {
                for (int i = 0; i < bytesRead; i++)
                {
                    byte b = buffer[i];
                    
                    if (!insideItem)
                    {
                        if (b == (byte)'{')
                        {
                            insideItem = true;
                            currentItemStart = absolutePosition + i;
                        }
                    }
                    else
                    {
                        if (b == (byte)'\n') 
                        {
                            long itemEnd = absolutePosition + i;
                            stepOffsets.Add(currentItemStart);
                            stepLengths.Add((int)(itemEnd - currentItemStart));
                            insideItem = false;
                        }
                    }
                }
                absolutePosition += bytesRead;
            }
            
            if (insideItem && currentItemStart != -1)
            {
                stepOffsets.Add(currentItemStart);
                stepLengths.Add((int)(absolutePosition - currentItemStart));
            }
        }

        TotalSteps = stepOffsets.Count;
        Debug.Log($"[ReplayDataReader] Index built. Total steps: {TotalSteps}");
    }

    public async Task<TrafficDataList> GetFrameAsync(int step, CancellationToken cancellationToken = default)
    {
        if (step < 0 || step >= TotalSteps) return null;
        
        await EnsureStepLoadedAsync(step, cancellationToken);
        
        if (activeChunk != null)
        {
            int localIndex = step - activeChunk.startStep;
            if (localIndex >= 0 && localIndex < activeChunk.frames.Count)
            {
                return activeChunk.frames[localIndex];
            }
        }
        return null;
    }

    private async Task EnsureStepLoadedAsync(int step, CancellationToken cancellationToken = default)
    {
        // 1. Current frame is within the active chunk
        if (activeChunk != null && step >= activeChunk.startStep && step <= activeChunk.endStep)
        {
            if (!isPrefetching && prefetchingChunk == null && activeChunk.endStep < TotalSteps - 1)
            {
                StartPrefetch(activeChunk.endStep + 1);
            }
            return;
        }

        // 2. Fall into prefetched chunk
        if (prefetchingChunk != null && step >= prefetchingChunk.startStep && step <= prefetchingChunk.endStep)
        {
            activeChunk = prefetchingChunk;
            prefetchingChunk = null; 
            
            if (activeChunk.endStep < TotalSteps - 1)
            {
                StartPrefetch(activeChunk.endStep + 1);
            }
            return;
        }

        // 3. Cache Miss - Load Asynchronously
        isPrefetching = true; // Prevent other fetches
        try
        {
            var chunk = await Task.Run(() => ReadChunkFromDisk(step, cancellationToken), cancellationToken);
            activeChunk = chunk;
            prefetchingChunk = null;
        }
        catch (OperationCanceledException)
        {
            // Task canceled, do not update activeChunk
        }
        finally
        {
            isPrefetching = false;
        }
        
        if (activeChunk != null && activeChunk.endStep < TotalSteps - 1)
        {
            StartPrefetch(activeChunk.endStep + 1);
        }
    }

    // Keep the old synchronous GetFrame? Yes, for ReplayCoroutine if we want, or change all to async.
    public TrafficDataList GetFrame(int step)
    {
        if (step < 0 || step >= TotalSteps) return null;
        
        EnsureStepLoaded(step);
        
        if (activeChunk != null)
        {
            int localIndex = step - activeChunk.startStep;
            if (localIndex >= 0 && localIndex < activeChunk.frames.Count)
            {
                return activeChunk.frames[localIndex];
            }
        }
        return null;
    }

    private void EnsureStepLoaded(int step)
    {
        // 1. Current frame is within the active chunk
        if (activeChunk != null && step >= activeChunk.startStep && step <= activeChunk.endStep)
        {
            if (!isPrefetching && prefetchingChunk == null && activeChunk.endStep < TotalSteps - 1)
            {
                StartPrefetch(activeChunk.endStep + 1);
            }
            return;
        }

        // 2. Fall into prefetched chunk
        if (prefetchingChunk != null && step >= prefetchingChunk.startStep && step <= prefetchingChunk.endStep)
        {
            activeChunk = prefetchingChunk;
            prefetchingChunk = null; 
            
            if (activeChunk.endStep < TotalSteps - 1)
            {
                StartPrefetch(activeChunk.endStep + 1);
            }
            return;
        }

        // 3. Cache Miss
        activeChunk = ReadChunkFromDisk(step);
        prefetchingChunk = null;
        isPrefetching = false;
        
        if (activeChunk.endStep < TotalSteps - 1)
        {
            StartPrefetch(activeChunk.endStep + 1);
        }
    }

    private async void StartPrefetch(int startStep)
    {
        isPrefetching = true;
        prefetchTargetStart = startStep;
        
        ChunkData result = await Task.Run(() => ReadChunkFromDisk(startStep));

        if (prefetchTargetStart == startStep) 
        {
            prefetchingChunk = result;
        }
        isPrefetching = false;
    }

    private ChunkData ReadChunkFromDisk(int startStep, CancellationToken cancellationToken = default)
    {
        ChunkData chunk = new ChunkData();
        chunk.startStep = startStep;
        chunk.endStep = startStep - 1;

        int currentBytes = 0;

        using (FileStream fs = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            for (int i = startStep; i < TotalSteps; i++)
            {
                cancellationToken.ThrowIfCancellationRequested();

                int len = stepLengths[i];
                if (currentBytes + len > MAX_CHUNK_BYTES && chunk.frames.Count > 0)
                {
                    break;
                }

                fs.Seek(stepOffsets[i], SeekOrigin.Begin);
                byte[] itemBytes = new byte[len];
                fs.Read(itemBytes, 0, len);
                
                string jsonStr = Encoding.UTF8.GetString(itemBytes).TrimEnd('\r', '\n', ',');
                var data = JsonConvert.DeserializeObject<TrafficDataList>(jsonStr);
                
                chunk.frames.Add(data);
                chunk.endStep = i;
                currentBytes += len;
            }
        }
        
        Debug.Log($"[ReplayDataReader] Loaded chunk from step {chunk.startStep} to {chunk.endStep} ({currentBytes / 1024f / 1024f:F2} MB)");
        return chunk;
    }
}