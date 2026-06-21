using System.Collections;
using System.Threading;
using TMPro;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

public class ReplayManager : MonoBehaviour
{
    [Header("Đường dẫn đến file replay")]
    [SerializeField] private ScriptPathSO scriptPathSO;
    [Header("UI Components")]
    [SerializeField] private Slider timeSlider;
    [SerializeField] private TMP_Text stepText;
    [SerializeField] private Button playButton;
    [SerializeField] private TMP_Text playButtonText;
    [SerializeField] private Button closeSimulationButton;
    private bool isPlaying = true;

    [Header("Events")]
    [SerializeField] private UnityEvent onLoadDataStart;
    [SerializeField] private UnityEvent onLoadDataEnd;
    [SerializeField] private UnityEvent onReplayEnd;

    [Header("Replay Settings")]
    [SerializeField] private float timeStep = 0.1f;
    [SerializeField, Min(0)] private int currentStep = 0;
    private int maxSteps = 0;

    private bool isCodeUpdatingSlider = false;
    private ReplayDataReader dataReader;
    private CancellationTokenSource loadCancellationTokenSource;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        currentStep = 0;
        dataReader = new ReplayDataReader(scriptPathSO.scriptPath);
        
        timeSlider.maxValue = dataReader.TotalSteps - 1;
        maxSteps = dataReader.TotalSteps - 1;
        timeSlider.value = currentStep;
        timeSlider.onValueChanged.AddListener(OnSliderValueChanged);
        playButton.onClick.AddListener(() => OnPlayButtonClicked(!isPlaying));
        closeSimulationButton.onClick.AddListener(() =>
        {
            Application.Quit();
        });
        StartCoroutine(ReplayCoroutine());
    }

    private async void OnSliderValueChanged(float value)
    {
        if (!isCodeUpdatingSlider)
        {
            // Hủy task cũ nếu người dùng kéo liên tục
            loadCancellationTokenSource?.Cancel();
            loadCancellationTokenSource = new CancellationTokenSource();

            onLoadDataStart?.Invoke();
            try
            {
                await SetStepAsync((int)value, true, loadCancellationTokenSource.Token);
                onLoadDataEnd?.Invoke();
            }
            catch (System.OperationCanceledException)
            {
                // Task bị hủy bởi lần kéo tiếp theo — onLoadDataEnd sẽ do task mới gọi
            }
        }
    }
    public void RestartReplay()
    {
        currentStep = 0;
        timeSlider.value = currentStep;
        isPlaying = true;
        playButtonText.text = "Tạm dừng";
        StartCoroutine(ReplayCoroutine());
    }

    // Update is called once per frame
    void Update()
    {
        
    }

    private IEnumerator ReplayCoroutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(timeStep);
            
            if (!isPlaying) continue;

            if (currentStep < dataReader.TotalSteps)
            {
                // Gọi async và đợi update để không đóng băng UI
                var task = SetStepAsync(currentStep, false, CancellationToken.None);
                yield return new WaitUntil(() => task.IsCompleted);
                
                isCodeUpdatingSlider = true;
                timeSlider.value = currentStep;
                isCodeUpdatingSlider = false;
                currentStep++;
            }
            else
            {
                isPlaying = false;
                onReplayEnd?.Invoke();
                if (CursorManager.Instance != null)
                {
                    CursorManager.Instance.UnlockCursor();
                }
                yield break;
            }
        }
    }

    private async System.Threading.Tasks.Task SetStepAsync(int step, bool isReplay, CancellationToken token)
    {
        if (step < 0 || step >= dataReader.TotalSteps) return;
        
        currentStep = step;
        
        var dataFrame = await dataReader.GetFrameAsync(currentStep, token);
        
        // Tránh nạp đè data lộn xộn nếu task này đã bị huỷ bởi task khác đến sau
        if (token.IsCancellationRequested) return;
        
        if (dataFrame != null)
        {
            TrafficerManager.Instance.ProcessData(dataFrame.Trafficers, isReplay);
            TrafficLightManager.Instance.ProcessData(dataFrame.TrafficLights);
            stepText.text = $"{currentStep}/{maxSteps}";
        }
    }
    public void SetTimeStep(float newTimeStep)
    {
        timeStep = newTimeStep;
    }
    private void OnPlayButtonClicked(bool isPlaying)
    {
        playButtonText.text = isPlaying ? "Tạm dừng" : "Tiếp tục";
        this.isPlaying = isPlaying;
    }

    private void OnDestroy()
    {
        loadCancellationTokenSource?.Cancel();
        loadCancellationTokenSource?.Dispose();
    }
}
