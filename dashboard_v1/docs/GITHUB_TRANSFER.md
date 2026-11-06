# Moving the dashboard to GitHub and IFBI VDI

## Option 1: GitHub browser upload (no local Git required)

Create or open an **approved private repository**, choose **Add file → Upload files**, then drag the extracted files/folders from this package into the GitHub browser upload (depending on your browser, you may need to upload folders separately). Commit the changes to an approved branch. On VDI, navigate to the repository and download the dashboard JSON using the Raw/Download control. Import it in Databricks Dashboards.

Do **not** upload the ZIP alone to GitHub expecting Databricks to import the ZIP. Databricks must receive an actual `.lvdash.json` file.

## Option 2: local Git (recommended for tracking changes)

From a terminal on a device allowed to access your company repository:

```bash
# Extract the supplied ZIP then enter the project folder
cd ifbi_genie_usage_dashboard_v1
# If your approved repository is already cloned, copy these files into it instead
# and run git add/commit/push there.
git init
git add README.md .gitignore dashboard docs sql tools tests
git commit -m "Add Genie usage observability dashboard v1"
# Connect to an EXISTING approved remote using the URL provided by your team:
# git remote add origin <your-approved-private-repo-url>
# git push -u origin <approved-branch>
```

No tokens, secrets, workspace hostnames, employee names, or private records are included in the repository. The workspace reads authorized Databricks system tables when the dashboard refreshes.
