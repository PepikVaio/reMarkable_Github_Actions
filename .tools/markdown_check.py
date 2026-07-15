import os
import subprocess

# =========================
# Check Markdown changes
# =========================
# Checks the last commit:
# - Deleted Markdown files (.md) -> stop workflow
# - Added or modified Markdown files -> continue workflow
# =======================================================
def main():
    # Get changed files between previous and current commit
    result = subprocess.run(
        ["git", "diff", "--name-status", "HEAD^", "HEAD"],
        capture_output=True,
        text=True
    )

    deleted_markdown = False

    # Check if any Markdown file was deleted
    for line in result.stdout.splitlines():
        # Git status:
        # D = deleted
        # M = modified
        # A = added
        if line.startswith("D") and line.endswith(".md"):
            deleted_markdown = True
            break

    # ==================================
    # Send result back to GitHub Actions
    # ==================================
    # true  -> workflow will stop
    # false -> workflow continues
    # ===========================
    if deleted_markdown:
        value = "true"
        print(" ")
        print("Markdown deleted")
    else:
        value = "false"
        print(" ")
        print("Markdown changed or added")

    # Write output for GitHub Actions
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"deleted={value}\n")

if __name__ == "__main__":
    main()

print(" ")
print("Done")