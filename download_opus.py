"""
自動下載並安裝 Opus 庫
用於修復 Discord 音樂機器人音頻播放問題
"""
import urllib.request
import os
import sys

def download_opus():
    print("開始下載 Opus 庫...")
    print("="*60)

    # Opus DLL 下載地址（來自 discord/opus 官方倉庫）
    opus_url = "https://github.com/discord/opus/releases/download/v1.5/opus.dll"

    # 保存到當前目錄
    opus_path = os.path.join(os.path.dirname(__file__), "opus.dll")

    try:
        # 檢查是否已存在
        if os.path.exists(opus_path):
            print(f"✓ opus.dll 已存在於: {opus_path}")
            user_input = input("是否要重新下載？(y/N): ")
            if user_input.lower() != 'y':
                print("取消下載。")
                return True

        # 下載文件
        print(f"正在從 {opus_url} 下載...")
        urllib.request.urlretrieve(opus_url, opus_path)

        # 驗證文件
        if os.path.exists(opus_path) and os.path.getsize(opus_path) > 0:
            file_size = os.path.getsize(opus_path) / 1024  # KB
            print(f"✓ 下載成功！")
            print(f"  文件位置: {opus_path}")
            print(f"  文件大小: {file_size:.2f} KB")
            print("\n現在可以重新啟動機器人了。")
            return True
        else:
            print("❌ 下載失敗：文件不完整")
            return False

    except Exception as e:
        print(f"❌ 下載失敗: {str(e)}")
        print("\n手動下載步驟：")
        print(f"1. 訪問: {opus_url}")
        print(f"2. 下載 opus.dll")
        print(f"3. 將文件放到: {os.path.dirname(__file__)}")
        return False
    finally:
        print("="*60)

if __name__ == "__main__":
    print("\nDiscord 音樂機器人 - Opus 庫下載工具")
    print("="*60)

    success = download_opus()

    if success:
        print("\n✓ 設置完成！請運行機器人:")
        print("  python main_onlymusic.py")
    else:
        print("\n❌ 設置失敗。請手動下載 opus.dll")

    input("\n按 Enter 鍵退出...")
