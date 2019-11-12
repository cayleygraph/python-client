import subprocess

subprocess.run(["python", "-m", "generate"], check=True)
subprocess.run(["pytest"], check=True)
