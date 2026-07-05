using Newtonsoft.Json;
using TMPro;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class PreRenderPreparer : MonoBehaviour
{
    [SerializeField] private RoadDataSO roadDataSO;
    [SerializeField] private ScriptPathSO scriptPathSO;
    [SerializeField] private TMP_InputField mapPathInputField;
    [SerializeField] private TMP_InputField scriptPathInputField;
    [SerializeField] private Button replayButton;
    [SerializeField] private TMP_Text errorText;

    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        // Tắt parse escape characters để tránh bug render khi path chứa \r, \n, \t...
        DisableEscapeParsing(mapPathInputField);
        DisableEscapeParsing(scriptPathInputField);

        mapPathInputField.onEndEdit.AddListener(path => mapPathInputField.text = CleanPath(path));
        scriptPathInputField.onEndEdit.AddListener(path => scriptPathInputField.text = CleanPath(path));

        replayButton.onClick.AddListener(() => {
            if (GetRoadData())
            {
                LoadPreRenderScene();
            }
        });
    }

    private bool IsValidFilePath(string path)
    {
        return !string.IsNullOrEmpty(path) && System.IO.File.Exists(path);
    }

    private bool GetRoadData()
    {
        if (!IsValidFilePath(mapPathInputField.text))
        {
            errorText.text = "Tệp bản đồ không hợp lệ.";
            errorText.color = Color.red;
            return false;
        }
        if (!IsValidFilePath(scriptPathInputField.text))
        {
            errorText.text = "Tệp kịch bản không hợp lệ.";
            errorText.color = Color.red;
            return false;
        }

        try
        {
            string mapJson = System.IO.File.ReadAllText(mapPathInputField.text);
            RoadData roadData = JsonConvert.DeserializeObject<RoadData>(mapJson);
            roadDataSO.junctionDatas = roadData.JunctionDatas;
            roadDataSO.edgeDatas = roadData.EdgeDatas;
            roadDataSO.crossingDatas = roadData.CrossingDatas;
            roadDataSO.buildingDatas = roadData.BuildingDatas;

            scriptPathSO.scriptPath = scriptPathInputField.text;

            replayButton.interactable = true;
            errorText.text = "";
            errorText.color = Color.white;
        }
        catch (System.Exception e)
        {
            errorText.text = $"Error loading data: {e.Message}";
            errorText.color = Color.red;
            return false;
        }
        return true;
    }

    #region Path Cleaning

    /// <summary>
    /// Hàm tổng làm sạch path: trim → bỏ quote → chuẩn hóa dấu phân cách.
    /// </summary>
    private string CleanPath(string path)
    {
        if (string.IsNullOrEmpty(path)) return path;

        path = TrimWhitespace(path);
        path = RemoveQuote(path);
        path = NormalizeSeparators(path);

        return path;
    }

    /// <summary>
    /// Xóa khoảng trắng đầu/cuối (khi paste path thường dính space thừa).
    /// </summary>
    private string TrimWhitespace(string path)
    {
        return path.Trim();
    }

    /// <summary>
    /// Bỏ dấu ngoặc kép bao quanh (khi copy "path" từ Windows Explorer / Shift+RClick).
    /// </summary>
    private string RemoveQuote(string path)
    {
        if (path.StartsWith("\""))
        {
            path = path[1..];
        }
        if (path.EndsWith("\""))
        {
            path = path[0..^1];
        }
        return path;
    }

    /// <summary>
    /// Chuyển backslash thành forward slash để tránh bug render TMP với \r \n \t...
    /// Windows vẫn hiểu '/' bình thường trong File API.
    /// </summary>
    private string NormalizeSeparators(string path)
    {
        return path.Replace('\\', '/');
    }

    /// <summary>
    /// Tắt parse escape characters trên TMP_InputField để text component không
    /// hiểu nhầm '\r' trong "D:\result\..." thành ký tự xuống dòng.
    /// </summary>
    private void DisableEscapeParsing(TMP_InputField input)
    {
        if (input.textComponent != null)
            input.textComponent.parseCtrlCharacters = false;

        if (input.placeholder is TMP_Text placeholder)
            placeholder.parseCtrlCharacters = false;
    }

    #endregion

    private void LoadPreRenderScene()
    {
        // Chuyển sang scene PreRender sau khi đã chuẩn bị xong dữ liệu, Scene có index là 2 trong Build Settings
        SceneManager.LoadScene(2);
    }
}