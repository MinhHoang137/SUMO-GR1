import os
import sys
import subprocess

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python git_commit.py <commit_message>")
        sys.exit(1)

    # Hỗ trợ thông điệp có dấu cách: ghép mọi tham số còn lại
    commit_message = " ".join(sys.argv[1:])

    def run(cmd, check=True, capture=False):
        return subprocess.run(
            cmd,
            check=check,
            text=True,
            capture_output=capture,
        )

    try:
        # Stage mọi thay đổi (thêm/xoá/sửa)
        run(["git", "add", "-A"])

        # Kiểm tra có gì để commit không
        diff = run(["git", "diff", "--cached", "--name-only"], capture=True)
        if not diff.stdout.strip():
            print("No staged changes to commit. Skipping commit.")
        else:
            # Commit với thông điệp an toàn (không cần tự thêm dấu nháy)
            run(["git", "commit", "-m", commit_message])

        # Lấy nhánh hiện tại
        branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True).stdout.strip()
        if not branch:
            branch = "main"

        # Đẩy lên origin, tạo upstream nếu chưa có
        run(["git", "push", "-u", "origin", branch], check=False)
    except subprocess.CalledProcessError as e:
        print("Git command failed:", e)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        sys.exit(e.returncode)
