using System;
using Unity.VisualScripting;
using UnityEngine;

public class CursorManager : MonoBehaviour
{
    [Header("Cursor Settings")]
    [SerializeField] private bool lockCursorOnStart = true;
    private bool lockable = true; // dùng để kiểm soát việc có thể khóa con trỏ hay không, tránh xung đột khi mở menu
    public static CursorManager Instance { get; private set; }
    private void Awake()
    {
        if (Instance != null)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        if (lockCursorOnStart)
        {
            LockCursor();
        }
        if (GameInput.Instance != null)
        {
            GameInput.Instance.OnMouseToggle += GameInput_OnToggleCursorLock;
        }

    }


    private void GameInput_OnToggleCursorLock(object sender, EventArgs e)
    {
        ToggleCursorLock();
    }


    // Update is called once per frame
    void Update()
    {
        
    }
    private void ToggleCursorLock()
    {
        if (Cursor.lockState == CursorLockMode.Locked)
        {
            UnlockCursor();
        }
        else
        {
            LockCursor();
        }
    }
    private void OnDestroy()
    {
        if (GameInput.Instance != null)
        {
            GameInput.Instance.OnMouseToggle -= GameInput_OnToggleCursorLock;
        }
        if (Instance == this)
        {
            Instance = null;
        }
    }
    public void LockCursor()
    {
        if (!lockable) return; // Nếu không cho phép khóa, thoát khỏi hàm
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }
    public void UnlockCursor()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }
    public bool IsCursorLocked()
    {
        return Cursor.lockState == CursorLockMode.Locked;
    }
    public void SetLockable(bool lockable)
    {
        this.lockable = lockable;
    }
}
