import subprocess

def run():
    result = subprocess.run(["git", "status"], capture_output=True, text=True)
    with open("git_status.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
    
    result2 = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True)
    with open("git_diff_cached.txt", "w", encoding="utf-8") as f:
        f.write(result2.stdout)
        
    result3 = subprocess.run(["git", "diff"], capture_output=True, text=True)
    with open("git_diff.txt", "w", encoding="utf-8") as f:
        f.write(result3.stdout)

if __name__ == "__main__":
    run()
