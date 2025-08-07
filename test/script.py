import time

for i in range(10):
    print("任务开始")
    with open("output.txt", "a", encoding="utf-8") as f:
        f.write(f"正在处理第{i+1}步\n")
    print(f"正在处理第{i+1}步")
    time.sleep(1)
