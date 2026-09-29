import re
src = open("main.py").read()

MAIN = '''def main():
    \'\'\'Main entry point for desktop app\'\'\'
    if sys.platform == 'win32':
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8')

    print('=' * 60)
    print('R3KON GPT - Cybersecurity Assistant ')
    print('=' * 60)
    port = find_free_port()
    print(f'Using port: {port}')
    print('Starting backend server...')
    threading.Thread(target=start_flask, args=(port,), daemon=True).start()
    print('Waiting for server to start...')
    if not wait_for_flask(port, timeout=120):
        print('ERROR: Server failed to start within the timeout')
        print('\\nTroubleshooting:')
        print("1. Check if model file exists in 'model' folder")
        print('2. Make sure llama-cpp-python is installed')
        print('3. Check console for error messages above')
        time.sleep(5)
        return
    print('Server started successfully!')
    print(f'Opening window at http://127.0.0.1:{port}')
    try:
        icon_path = get_resource_path('icon.ico')
        if not os.path.exists(icon_path):
            icon_path = get_resource_path('icon.png')
        webview.create_window('R3KON GPT - Cybersecurity Assistant',
                              f'http://127.0.0.1:{port}', width=1400, height=900)
        print('Window created!')
        webview.start()
    except Exception as e:
        print(f'ERROR: Failed to create window: {e}')
        import traceback
        traceback.print_exc()
        time.sleep(5)


if __name__ == '__main__':
    main()
'''
new, n = re.subn(r"\ndef main\(\):.*\Z", "\n" + MAIN, src, flags=re.S)
print("main replaced:", n)
open("main.py", "w").write(new)
