using System;
using System.Collections.Generic;
using UnityEngine;

public class UIManager : MonoBehaviour
{
    public static UIManager Instance { get; private set; }
    // Khai báo một Stack để chứa các GameObject là các UI Panel
    private Stack<GameObject> menuStack = new Stack<GameObject>();

    [SerializeField] private GameObject mainMenuPanel; // Gán panel chính trong Inspector

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
        }
    }
    private void Start()
    {
        GameInput.Instance.OnToggleOptions += HandleEscPressed; // Đăng ký sự kiện khi người chơi nhấn phím Esc
    }

    private void HandleEscPressed(object sender, EventArgs e)
    {
        if (menuStack.Count > 0)
        {
            CloseCurrentMenu(); // Đóng menu hiện tại nếu có
        }
        else
        {
            OpenMenu(mainMenuPanel); // Mở menu chính nếu không có menu nào đang mở
        }
    }

    // Gọi hàm này khi muốn mở một UI Panel mới (Push)
    public void OpenMenu(GameObject menuToOpen)
    {
        if (menuToOpen == null) return; // Kiểm tra nếu menuToOpen là null thì không làm gì
        // CursorManager.Instance.UnlockCursor(); // Mở khóa con trỏ chuột khi mở menu
        // Nếu đang có một menu mở, hãy tạm ẩn nó đi (tuỳ logic game)
        if (menuStack.Count > 0)
        {
            menuStack.Peek().SetActive(false); 
        }

        // Đẩy menu mới lên đỉnh Stack và bật nó lên
        menuStack.Push(menuToOpen);
        menuToOpen.SetActive(true);
    }

    // Gọi hàm này khi bấm nút "Back" hoặc "Close" (Pop)
    public void CloseCurrentMenu()
    {
        if (menuStack.Count > 0)
        {
            // Lấy menu trên đỉnh ra và tắt nó đi
            GameObject currentMenu = menuStack.Pop();
            currentMenu.SetActive(false);

            // Bật lại menu nằm ngay bên dưới (nếu có)
            if (menuStack.Count > 0)
            {
                menuStack.Peek().SetActive(true);
            } else
            {
                CursorManager.Instance.LockCursor(); // Khóa con trỏ chuột khi không còn menu nào mở
            }
        }
    }
    public void CloseMenu(GameObject menuToClose)
    {
        if (menuToClose == null) return; // Kiểm tra nếu menuToClose là null thì không làm gì
        if (menuStack.Contains(menuToClose))
        {
            // Tạo một Stack tạm để giữ các menu khác
            Stack<GameObject> tempStack = new Stack<GameObject>();

            // Pop các menu cho đến khi tìm thấy menu cần đóng
            while (menuStack.Count > 0)
            {
                GameObject currentMenu = menuStack.Pop();
                if (currentMenu == menuToClose)
                {
                    currentMenu.SetActive(false); // Tắt menu cần đóng
                    break;
                }
                else
                {
                    tempStack.Push(currentMenu); // Lưu các menu khác vào Stack tạm
                }
            }

            // Đẩy lại các menu còn lại từ Stack tạm về Stack chính
            while (tempStack.Count > 0)
            {
                GameObject tempMenu = tempStack.Pop();
                menuStack.Push(tempMenu);
            }

            // Bật lại menu trên đỉnh nếu có
            if (menuStack.Count > 0)
            {
                menuStack.Peek().SetActive(true);
            } else
            {
                CursorManager.Instance.LockCursor(); // Khóa con trỏ chuột khi không còn menu nào mở
            }
        }
    }
    void OnDestroy()
    {
        if (GameInput.Instance != null)
        {
            GameInput.Instance.OnToggleOptions -= HandleEscPressed; // Hủy đăng ký sự kiện khi đối tượng bị hủy để tránh lỗi
        }
        if (Instance == this){
            Instance = null; // Hủy tham chiếu đến Instance khi đối tượng bị hủy
        }
    }
    
}