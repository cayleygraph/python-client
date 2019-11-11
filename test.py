import subprocess

subprocess.call(["python", "-m", "generate"])
subprocess.call(["pytest"])
