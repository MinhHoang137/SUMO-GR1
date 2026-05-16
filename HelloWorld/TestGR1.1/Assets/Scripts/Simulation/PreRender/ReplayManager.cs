using System.Collections;
using System.Threading;
using UnityEngine;
using UnityEngine.UI;

public class ReplayManager : MonoBehaviour
{
    [SerializeField] private ScriptPathSO scriptPathSO;
    [SerializeField] private Slider timeSlider;
    [SerializeField] private float timeStep = 0.1f;
    [SerializeField, Min(0)] private int currentStep = 0;

    private bool isCodeUpdatingSlider = false;
    private ReplayDataReader dataReader;
    private CancellationTokenSource loadCancellationTokenSource;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        currentStep = 0;
        dataReader = new ReplayDataReader(scriptPathSO.scriptPath);
        
        timeSlider.maxValue = dataReader.TotalSteps - 1;
        timeSlider.value = currentStep;
        timeSlider.onValueChanged.AddListener(OnSliderValueChanged);
        
        StartCoroutine(ReplayCoroutine());
    }

    private async void OnSliderValueChanged(float value)
    {
        if (!isCodeUpdatingSlider)
        {
            // Hủy task cũ nếu người dùng kéo liên tục
            loadCancellationTokenSource?.Cancel();
            loadCancellationTokenSource = new CancellationTokenSource();
            
            try
            {
                await SetStepAsync((int)value, true, loadCancellationTokenSource.Token);
            }
            catch (System.OperationCanceledException)
            {
                // Bỏ qua lỗi do bị hủy
            }
        }
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
                // break; // Hết dữ liệu thì dừng
                continue; // Hoặc loop lại từ đầu nếu muốn
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
        }
    }
    public void SetTimeStep(float newTimeStep)
    {
        timeStep = newTimeStep;
    }

    private void OnDestroy()
    {
        loadCancellationTokenSource?.Cancel();
        loadCancellationTokenSource?.Dispose();
    }
}
