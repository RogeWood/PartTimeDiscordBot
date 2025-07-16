# PartTimeDiscordBot
工作室的無情打卡機機器人 

> 使用 `/help` 查看指令說明

---

<img width="467" height="402" alt="螢幕擷取畫面 2025-07-16 165124" src="https://github.com/user-attachments/assets/63d1ac85-7806-43b3-8381-215170ddbd3b" />


## 🛠 開發資訊

* **開發語言**：Python 3
* **使用函式庫**：Nextcord 2.6.0

---

## 📦 功能一覽

### 一般指令

* `/bot`：機器人介紹
* `/ping`：延遲測試
* `/user_info`：使用者資訊
* `/purge`：清除訊息（管理員）

### 會議管理 (/meeting)

* `add`：新增單次會議
* `weekly`：設定每週固定會議
* `remove_single`：刪除單次會議
* `remove_weekly`：關閉每週會議
* `list`：列出所有會議
* `set_channel`：設定提醒頻道
* `set_reminder`：設定提前提醒
* `clear_reminders`：關閉所有提醒

### 請假系統 (/leave)

* `add`：新增請假紀錄
* `list`：列出請假紀錄
* `remove`：刪除請假紀錄
* `set_channel`：設定公告頻道
* `set_time`：設定公告時間

### 打卡系統 (/work)

* `set_channel`：設定打卡頻道
* `checkin`：上班打卡
* `checkout`：下班打卡
* `duration`：查詢工時
* `menu`：顯示按鈕選單
* `list`：列出紀錄及加總
* `clear_log`：清除紀錄

### 其他功能

* **會議提醒排程**：自動提前提醒設定時間的會議
* **請假公告排程**：每天指定時間發布當日請假公告
* **開機自動執行**：是否清空頻道、發送打卡 UI 訊息
---

## 📂 安裝與設定

1. 將專案 clone 至本地：

   ```bash
   git clone <repo_url>
   cd PartTimeDiscordBot
   ```

2. 安裝相依套件：

   ```bash
   pip install -r requirements.txt
   ```
3. 在專案根目錄中，將 `env` 更改名稱 `.env` 檔案（與 `main.py` 同目錄），並填入：

   ```env
   BOT_TOKEN=你的BotToken
   BOOT_CHANNEL_ID=你的會議提醒頻道ID
   DISCORD_SERVER_ID=你的伺服器ID
   IS_CLEAR_BOOT_CHANNEL=True/False(是否清空機器人啟動訊息的頻道)
   ```
4. 編輯 `data/config.json`：

   ```json
   {
     "reminder_minutes": [提前提醒秒數...],
     "leave_announcement_time": {"hour": 9, "minute": 0}
   }
   ```
5. 啟動 Bot：

   ```bash
   python main.py
   ```

## 開機時自動運行
複製 `DiscorBotAutoStart.txt` 到以下路徑'C:\Users\{Your_Windows_User_Name}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'  (win + R 搜尋 shell:startup)

將專案與 pythonw 的路徑更改成自己的
```bash
@echo off
start "" @echo off
cd /d "{Yout_Project_Path}"
start "" "{Your_pythonw_path}" "main.py"
```

將檔案名稱的副檔名改成 `.bat` EX: `DiscorBotAutoStart.bat` 

**關閉程式:** 開啟工作管理員，找到正在執行的 python 關閉即可
